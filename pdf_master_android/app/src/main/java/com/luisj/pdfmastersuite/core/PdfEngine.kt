package com.luisj.pdfmastersuite.core

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.provider.OpenableColumns
import com.luisj.pdfmastersuite.core.models.*
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.io.MemoryUsageSetting
import com.tom_roush.pdfbox.multipdf.PDFMergerUtility
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.pdmodel.PDPageContentStream
import com.tom_roush.pdfbox.pdmodel.common.PDRectangle
import com.tom_roush.pdfbox.pdmodel.encryption.AccessPermission
import com.tom_roush.pdfbox.pdmodel.encryption.StandardProtectionPolicy
import com.tom_roush.pdfbox.pdmodel.font.PDType1Font
import com.tom_roush.pdfbox.pdmodel.graphics.image.LosslessFactory
import com.tom_roush.pdfbox.pdmodel.graphics.state.PDExtendedGraphicsState
import com.tom_roush.pdfbox.text.PDFTextStripper
import com.tom_roush.pdfbox.util.Matrix
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.InputStream
import java.io.OutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * Motor central de procesamiento y manipulación de archivos PDF e imágenes en Android.
 * Reemplazo nativo en Kotlin de 'pdf_tools.py'.
 */
object PdfEngine {

    private var isInitialized = false

    fun init(context: Context) {
        if (!isInitialized) {
            PDFBoxResourceLoader.init(context.applicationContext)
            isInitialized = true
        }
    }

    // -------------------------------------------------------------------------
    // INFORMACIÓN Y METADATOS
    // -------------------------------------------------------------------------

    fun getFileDetails(context: Context, uri: Uri): DocumentFileItem {
        var displayName = "Documento.pdf"
        var sizeBytes = 0L

        context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            val sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE)
            if (cursor.moveToFirst()) {
                if (nameIndex != -1) displayName = cursor.getString(nameIndex) ?: displayName
                if (sizeIndex != -1) sizeBytes = cursor.getLong(sizeIndex)
            }
        }

        var pageCount: Int? = null
        var isEncrypted = false

        try {
            context.contentResolver.openInputStream(uri)?.use { stream ->
                PDDocument.load(stream).use { doc ->
                    isEncrypted = doc.isEncrypted
                    pageCount = doc.numberOfPages
                }
            }
        } catch (e: Exception) {
            // Podría estar protegido o ser una imagen
        }

        return DocumentFileItem(
            uri = uri,
            name = displayName,
            sizeBytes = sizeBytes,
            pageCount = pageCount,
            isEncrypted = isEncrypted
        )
    }

    // -------------------------------------------------------------------------
    // 1. UNIR PDFs (MERGE)
    // -------------------------------------------------------------------------

    suspend fun mergePdfs(
        context: Context,
        pdfUris: List<Uri>,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        require(pdfUris.size >= 2) { "Se necesitan al menos 2 archivos PDF para unir." }

        val merger = PDFMergerUtility()
        val openStreams = mutableListOf<InputStream>()

        try {
            pdfUris.forEach { uri ->
                val stream = context.contentResolver.openInputStream(uri)
                    ?: throw IllegalArgumentException("No se pudo leer el archivo: $uri")
                openStreams.add(stream)
                merger.addSource(stream)
            }
            merger.destinationStream = outputStream
            merger.mergeDocuments(MemoryUsageSetting.setupMainMemoryOnly())
        } finally {
            openStreams.forEach {
                try { it.close() } catch (_: Exception) {}
            }
            try { outputStream.close() } catch (_: Exception) {}
        }
    }

    // -------------------------------------------------------------------------
    // 2. DIVIDIR PDF (SPLIT)
    // -------------------------------------------------------------------------

    fun parsePageRanges(rangeStr: String, totalPages: Int): List<Int> {
        val clean = rangeStr.replace(" ", "")
        if (clean.isBlank()) return emptyList()

        val pages = mutableSetOf<Int>()
        val parts = clean.split(",")

        for (part in parts) {
            if (part.contains("-")) {
                val sub = part.split("-")
                require(sub.size == 2) { "Rango no válido: $part" }
                val start = sub[0].toIntOrNull() ?: throw IllegalArgumentException("Inicio no válido: $part")
                val end = sub[1].toIntOrNull() ?: throw IllegalArgumentException("Fin no válido: $part")
                require(start in 1..totalPages && end in 1..totalPages) {
                    "Rango $part fuera de límites (1 a $totalPages)."
                }
                require(start <= end) { "En el rango '$part', el inicio no puede ser mayor al final." }
                for (p in start..end) pages.add(p - 1)
            } else {
                val page = part.toIntOrNull() ?: throw IllegalArgumentException("Página no válida: $part")
                require(page in 1..totalPages) { "Página $page fuera de límites (1 a $totalPages)." }
                pages.add(page - 1)
            }
        }
        return pages.sorted()
    }

    suspend fun splitPdfByRanges(
        context: Context,
        sourceUri: Uri,
        rangeStr: String,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo abrir el archivo de origen.")

        PDDocument.load(inStream).use { srcDoc ->
            val totalPages = srcDoc.numberOfPages
            val selectedPages = parsePageRanges(rangeStr, totalPages)
            require(selectedPages.isNotEmpty()) { "Debe seleccionar al menos una página para exportar." }

            PDDocument().use { outDoc ->
                for (pageIdx in selectedPages) {
                    outDoc.addPage(srcDoc.getPage(pageIdx))
                }
                outDoc.save(outputStream)
            }
        }
        outputStream.close()
    }

    // -------------------------------------------------------------------------
    // 3. ORGANIZAR Y ROTAR (RENDERIZADO Y EXPORTACIÓN)
    // -------------------------------------------------------------------------

    suspend fun renderThumbnails(
        context: Context,
        pdfUri: Uri,
        maxPages: Int = 120
    ): List<PdfPageItem> = withContext(Dispatchers.IO) {
        val result = mutableListOf<PdfPageItem>()
        val pfd = context.contentResolver.openFileDescriptor(pdfUri, "r")
            ?: return@withContext emptyList()

        try {
            PdfRenderer(pfd).use { renderer ->
                val count = minOf(renderer.pageCount, maxPages)
                for (i in 0 until count) {
                    val page = renderer.openPage(i)
                    // Renderizamos con un tamaño amigable para memoria (ancho objetivo ~300px)
                    val targetWidth = 320
                    val targetHeight = ((targetWidth.toFloat() / page.width) * page.height).toInt().coerceAtLeast(100)

                    val bitmap = Bitmap.createBitmap(targetWidth, targetHeight, Bitmap.Config.ARGB_8888)
                    page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                    page.close()

                    result.add(
                        PdfPageItem(
                            originalPageIndex = i,
                            displayPageNumber = i + 1,
                            rotationDegrees = 0,
                            thumbnail = bitmap
                        )
                    )
                }
            }
        } finally {
            pfd.close()
        }
        result
    }

    suspend fun exportRearrangedPdf(
        context: Context,
        sourceUri: Uri,
        pageItems: List<PdfPageItem>,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo leer el archivo original.")

        PDDocument.load(inStream).use { srcDoc ->
            PDDocument().use { outDoc ->
                for (item in pageItems) {
                    if (item.isMarkedForDeletion) continue

                    val page = srcDoc.getPage(item.originalPageIndex)
                    if (item.rotationDegrees != 0) {
                        val currentRotation = page.rotation
                        page.rotation = (currentRotation + item.rotationDegrees) % 360
                    }
                    outDoc.addPage(page)
                }
                outDoc.save(outputStream)
            }
        }
        outputStream.close()
    }

    // -------------------------------------------------------------------------
    // 4. IMÁGENES A PDF
    // -------------------------------------------------------------------------

    suspend fun imagesToPdf(
        context: Context,
        imageUris: List<Uri>,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        require(imageUris.isNotEmpty()) { "Debe seleccionar al menos una imagen." }
        val document = android.graphics.pdf.PdfDocument()

        try {
            imageUris.forEachIndexed { index, uri ->
                val inStream = context.contentResolver.openInputStream(uri)
                    ?: return@forEachIndexed

                // Muestreo para evitar OutOfMemory en fotos de 50 Megapixeles
                val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                BitmapFactory.decodeStream(inStream, null, options)
                inStream.close()

                val maxDimension = 1920
                var sampleSize = 1
                while (options.outWidth / sampleSize > maxDimension || options.outHeight / sampleSize > maxDimension) {
                    sampleSize *= 2
                }

                val decodeStream = context.contentResolver.openInputStream(uri)
                val decodeOptions = BitmapFactory.Options().apply { inSampleSize = sampleSize }
                val bitmap = BitmapFactory.decodeStream(decodeStream, null, decodeOptions)
                decodeStream?.close()

                if (bitmap != null) {
                    val pageInfo = android.graphics.pdf.PdfDocument.PageInfo.Builder(
                        bitmap.width,
                        bitmap.height,
                        index + 1
                    ).create()

                    val page = document.startPage(pageInfo)
                    page.canvas.drawBitmap(bitmap, 0f, 0f, null)
                    document.finishPage(page)
                    bitmap.recycle()
                }
            }
            document.writeTo(outputStream)
        } finally {
            document.close()
            outputStream.close()
        }
    }

    // -------------------------------------------------------------------------
    // 5. SEGURIDAD (PROTEGER / DESBLOQUEAR)
    // -------------------------------------------------------------------------

    suspend fun protectPdf(
        context: Context,
        sourceUri: Uri,
        password: String,
        algorithm: EncryptionAlgorithm,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        require(password.isNotBlank()) { "La contraseña no puede estar vacía." }

        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo leer el archivo de origen.")

        PDDocument.load(inStream).use { doc ->
            val ap = AccessPermission()
            val spp = StandardProtectionPolicy(password, password, ap)
            spp.encryptionKeyLength = algorithm.keyLength
            spp.permissions = ap
            doc.protect(spp)
            doc.save(outputStream)
        }
        outputStream.close()
    }

    suspend fun unlockPdf(
        context: Context,
        sourceUri: Uri,
        password: String,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo leer el archivo de origen.")

        PDDocument.load(inStream, password).use { doc ->
            doc.isAllSecurityToBeRemoved = true
            doc.save(outputStream)
        }
        outputStream.close()
    }

    // -------------------------------------------------------------------------
    // 6. COMPRIMIR PDF
    // -------------------------------------------------------------------------

    suspend fun compressPdf(
        context: Context,
        sourceUri: Uri,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo leer el archivo.")

        PDDocument.load(inStream).use { doc ->
            // Optimización de flujos y eliminación de metadatos redundantes
            doc.documentCatalog.metadata = null
            doc.save(outputStream)
        }
        outputStream.close()
    }

    // -------------------------------------------------------------------------
    // 7. PDF A IMÁGENES (EXPORTAR JPG/PNG)
    // -------------------------------------------------------------------------

    suspend fun pdfToImages(
        context: Context,
        pdfUri: Uri,
        format: ImageExportFormat,
        scale: Float = 2.0f,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        val pfd = context.contentResolver.openFileDescriptor(pdfUri, "r")
            ?: throw IllegalArgumentException("No se pudo abrir el archivo PDF.")

        try {
            PdfRenderer(pfd).use { renderer ->
                val pageCount = renderer.pageCount
                require(pageCount > 0) { "El documento PDF está vacío." }

                val compressFormat = if (format == ImageExportFormat.PNG) {
                    Bitmap.CompressFormat.PNG
                } else {
                    Bitmap.CompressFormat.JPEG
                }
                val quality = if (format == ImageExportFormat.PNG) 100 else 90

                if (pageCount == 1) {
                    val page = renderer.openPage(0)
                    val width = (page.width * scale).toInt().coerceAtLeast(100)
                    val height = (page.height * scale).toInt().coerceAtLeast(100)
                    val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
                    page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                    page.close()

                    bitmap.compress(compressFormat, quality, outputStream)
                    bitmap.recycle()
                } else {
                    // Si son múltiples páginas, empaquetar en ZIP directamente al OutputStream
                    ZipOutputStream(outputStream).use { zipOut ->
                        for (i in 0 until pageCount) {
                            val page = renderer.openPage(i)
                            val width = (page.width * scale).toInt().coerceAtLeast(100)
                            val height = (page.height * scale).toInt().coerceAtLeast(100)
                            val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
                            page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                            page.close()

                            val entryName = "pagina_%03d.${format.extension}".format(i + 1)
                            zipOut.putNextEntry(ZipEntry(entryName))
                            bitmap.compress(compressFormat, quality, zipOut)
                            zipOut.closeEntry()
                            bitmap.recycle()
                        }
                    }
                }
            }
        } finally {
            pfd.close()
            try { outputStream.close() } catch (_: Exception) {}
        }
    }

    // -------------------------------------------------------------------------
    // 8. MARCA DE AGUA (TEXTO O IMAGEN)
    // -------------------------------------------------------------------------

    suspend fun addWatermark(
        context: Context,
        sourceUri: Uri,
        text: String,
        imageUri: Uri? = null,
        opacity: Float = 0.35f,
        angleDegrees: Float = 45f,
        fontSize: Float = 48f,
        colorRgb: Triple<Float, Float, Float> = Triple(0.5f, 0.5f, 0.5f),
        position: WatermarkPosition = WatermarkPosition.DIAGONAL,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo leer el archivo de origen.")

        PDDocument.load(inStream).use { doc ->
            val extState = PDExtendedGraphicsState().apply {
                nonStrokingAlphaConstant = opacity.coerceIn(0.05f, 1.0f)
            }

            var watermarkBitmap: Bitmap? = null
            if (imageUri != null) {
                context.contentResolver.openInputStream(imageUri)?.use { stream ->
                    watermarkBitmap = BitmapFactory.decodeStream(stream)
                }
            }

            for (page in doc.pages) {
                val mediaBox = page.mediaBox
                val pageWidth = mediaBox.width
                val pageHeight = mediaBox.height

                PDPageContentStream(doc, page, PDPageContentStream.AppendMode.APPEND, true, true).use { cs ->
                    cs.setGraphicsStateParameters(extState)

                    if (watermarkBitmap != null) {
                        val pdImage = LosslessFactory.createFromImage(doc, watermarkBitmap)
                        val imgWidth = pageWidth * 0.5f
                        val imgHeight = imgWidth * (watermarkBitmap!!.height.toFloat() / watermarkBitmap!!.width.toFloat())
                        val posX = (pageWidth - imgWidth) / 2f
                        val posY = (pageHeight - imgHeight) / 2f
                        cs.drawImage(pdImage, posX, posY, imgWidth, imgHeight)
                    } else if (text.isNotBlank()) {
                        val font = PDType1Font.HELVETICA_BOLD
                        cs.setFont(font, fontSize)
                        cs.setNonStrokingColor(colorRgb.first, colorRgb.second, colorRgb.third)

                        val textWidth = font.getStringWidth(text) / 1000f * fontSize
                        val rad = Math.toRadians(angleDegrees.toDouble())

                        val centerX = pageWidth / 2f
                        val centerY = pageHeight / 2f

                        val (tx, ty) = when (position) {
                            WatermarkPosition.CENTER -> Pair((pageWidth - textWidth) / 2f, pageHeight / 2f)
                            WatermarkPosition.TOP_CENTER -> Pair((pageWidth - textWidth) / 2f, pageHeight - 70f)
                            WatermarkPosition.BOTTOM_CENTER -> Pair((pageWidth - textWidth) / 2f, 70f)
                            WatermarkPosition.DIAGONAL -> Pair(centerX, centerY)
                        }

                        if (position == WatermarkPosition.DIAGONAL || angleDegrees != 0f) {
                            val matrix = Matrix()
                            matrix.translate(tx, ty)
                            matrix.rotate(rad)
                            matrix.translate(-textWidth / 2f, 0f)
                            cs.setTextMatrix(matrix)
                            cs.beginText()
                            cs.showText(text)
                            cs.endText()
                        } else {
                            cs.beginText()
                            cs.newLineAtOffset(tx, ty)
                            cs.showText(text)
                            cs.endText()
                        }
                    }
                }
            }
            watermarkBitmap?.recycle()
            doc.save(outputStream)
        }
        outputStream.close()
    }

    // -------------------------------------------------------------------------
    // 9. NUMERAR PÁGINAS
    // -------------------------------------------------------------------------

    suspend fun addPageNumbers(
        context: Context,
        sourceUri: Uri,
        format: PageNumberFormat,
        position: PageNumberPosition,
        fontSize: Float = 11f,
        skipCover: Boolean = true,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo leer el archivo de origen.")

        PDDocument.load(inStream).use { doc ->
            val totalPages = doc.numberOfPages
            val font = PDType1Font.HELVETICA

            for (i in 0 until totalPages) {
                if (skipCover && i == 0) continue

                val page = doc.getPage(i)
                val mediaBox = page.mediaBox
                val pageWidth = mediaBox.width
                val pageHeight = mediaBox.height

                val pageNum = if (skipCover) i else i + 1
                val totalDisplay = if (skipCover) totalPages - 1 else totalPages

                val text = when (format) {
                    PageNumberFormat.PAG_X -> "Pág. $pageNum"
                    PageNumberFormat.X_DE_Y -> "$pageNum de $totalDisplay"
                    PageNumberFormat.DASHES -> "- $pageNum -"
                    PageNumberFormat.ONLY_X -> "$pageNum"
                }

                val textWidth = font.getStringWidth(text) / 1000f * fontSize
                val margin = 36f

                val (x, y) = when (position) {
                    PageNumberPosition.BOTTOM_CENTER -> Pair((pageWidth - textWidth) / 2f, margin)
                    PageNumberPosition.BOTTOM_RIGHT -> Pair(pageWidth - textWidth - margin, margin)
                    PageNumberPosition.BOTTOM_LEFT -> Pair(margin, margin)
                    PageNumberPosition.TOP_CENTER -> Pair((pageWidth - textWidth) / 2f, pageHeight - margin)
                    PageNumberPosition.TOP_RIGHT -> Pair(pageWidth - textWidth - margin, pageHeight - margin)
                }

                PDPageContentStream(doc, page, PDPageContentStream.AppendMode.APPEND, true, true).use { cs ->
                    cs.setFont(font, fontSize)
                    cs.setNonStrokingColor(0.2f, 0.2f, 0.2f)
                    cs.beginText()
                    cs.newLineAtOffset(x, y)
                    cs.showText(text)
                    cs.endText()
                }
            }
            doc.save(outputStream)
        }
        outputStream.close()
    }

    // -------------------------------------------------------------------------
    // 10. ROTAR EN BLOQUE
    // -------------------------------------------------------------------------

    suspend fun rotateBulk(
        context: Context,
        sourceUri: Uri,
        degrees: Int,
        filter: RotateFilter,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo leer el archivo de origen.")

        PDDocument.load(inStream).use { doc ->
            for (i in 0 until doc.numberOfPages) {
                val pageNumber = i + 1
                val shouldRotate = when (filter) {
                    RotateFilter.ALL -> true
                    RotateFilter.EVEN -> pageNumber % 2 == 0
                    RotateFilter.ODD -> pageNumber % 2 != 0
                }
                if (shouldRotate) {
                    val page = doc.getPage(i)
                    page.rotation = (page.rotation + degrees) % 360
                }
            }
            doc.save(outputStream)
        }
        outputStream.close()
    }

    // -------------------------------------------------------------------------
    // 11. PDF A TEXTO
    // -------------------------------------------------------------------------

    suspend fun extractText(
        context: Context,
        sourceUri: Uri
    ): String = withContext(Dispatchers.IO) {
        init(context)
        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo leer el archivo de origen.")

        PDDocument.load(inStream).use { doc ->
            val stripper = PDFTextStripper()
            stripper.sortByPosition = true
            stripper.getText(doc)
        }
    }

    suspend fun saveTextToFile(
        text: String,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        outputStream.bufferedWriter(Charsets.UTF_8).use { writer ->
            writer.write(text)
        }
    }

    // -------------------------------------------------------------------------
    // 12. RECORTAR PDF (MÁRGENES)
    // -------------------------------------------------------------------------

    suspend fun cropMargins(
        context: Context,
        sourceUri: Uri,
        topMm: Float,
        bottomMm: Float,
        leftMm: Float,
        rightMm: Float,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo leer el archivo de origen.")

        val mmToPt = 2.83465f
        val topPt = topMm * mmToPt
        val bottomPt = bottomMm * mmToPt
        val leftPt = leftMm * mmToPt
        val rightPt = rightMm * mmToPt

        PDDocument.load(inStream).use { doc ->
            for (page in doc.pages) {
                val mediaBox = page.mediaBox
                val newX = mediaBox.lowerLeftX + leftPt
                val newY = mediaBox.lowerLeftY + bottomPt
                val newWidth = mediaBox.width - (leftPt + rightPt)
                val newHeight = mediaBox.height - (topPt + bottomPt)

                if (newWidth > 36f && newHeight > 36f) {
                    page.cropBox = PDRectangle(newX, newY, newWidth, newHeight)
                }
            }
            doc.save(outputStream)
        }
        outputStream.close()
    }

    // -------------------------------------------------------------------------
    // 13. FIRMAR PDF (ESTAMPAR FIRMA TÁCTIL)
    // -------------------------------------------------------------------------

    suspend fun stampSignature(
        context: Context,
        sourceUri: Uri,
        pageIndex: Int,
        signatureBitmap: Bitmap,
        posXRatio: Float = 0.60f,
        posYRatio: Float = 0.08f,
        targetWidthRatio: Float = 0.32f,
        outputStream: OutputStream
    ) = withContext(Dispatchers.IO) {
        init(context)
        val inStream = context.contentResolver.openInputStream(sourceUri)
            ?: throw IllegalArgumentException("No se pudo leer el archivo de origen.")

        PDDocument.load(inStream).use { doc ->
            val pageCount = doc.numberOfPages
            require(pageIndex in 0 until pageCount) { "Página seleccionada fuera de rango ($pageIndex de $pageCount)." }

            val page = doc.getPage(pageIndex)
            val mediaBox = page.mediaBox
            val pageWidth = mediaBox.width
            val pageHeight = mediaBox.height

            val sigWidth = pageWidth * targetWidthRatio
            val sigHeight = sigWidth * (signatureBitmap.height.toFloat() / signatureBitmap.width.toFloat())

            val sigX = pageWidth * posXRatio
            val sigY = pageHeight * posYRatio

            val pdImage = LosslessFactory.createFromImage(doc, signatureBitmap)

            PDPageContentStream(doc, page, PDPageContentStream.AppendMode.APPEND, true, true).use { cs ->
                cs.drawImage(pdImage, sigX, sigY, sigWidth, sigHeight)
            }
            doc.save(outputStream)
        }
        outputStream.close()
    }
}

