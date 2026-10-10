package com.luisj.pdfmastersuite.ui.viewmodel

import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.luisj.pdfmastersuite.core.AppUpdateInfo
import com.luisj.pdfmastersuite.core.PdfEngine
import com.luisj.pdfmastersuite.core.UpdateChecker
import com.luisj.pdfmastersuite.core.models.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.OutputStream

class PdfToolViewModel : ViewModel() {

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _loadingMessage = MutableStateFlow("Procesando documento...")
    val loadingMessage: StateFlow<String> = _loadingMessage.asStateFlow()

    private val _selectedFiles = MutableStateFlow<List<DocumentFileItem>>(emptyList())
    val selectedFiles: StateFlow<List<DocumentFileItem>> = _selectedFiles.asStateFlow()

    private val _singleFile = MutableStateFlow<DocumentFileItem?>(null)
    val singleFile: StateFlow<DocumentFileItem?> = _singleFile.asStateFlow()

    private val _pdfPages = MutableStateFlow<List<PdfPageItem>>(emptyList())
    val pdfPages: StateFlow<List<PdfPageItem>> = _pdfPages.asStateFlow()

    private val _extractedText = MutableStateFlow("")
    val extractedText: StateFlow<String> = _extractedText.asStateFlow()

    private val _result = MutableStateFlow<OperationResult?>(null)
    val result: StateFlow<OperationResult?> = _result.asStateFlow()

    private val _updateInfo = MutableStateFlow<AppUpdateInfo?>(null)
    val updateInfo: StateFlow<AppUpdateInfo?> = _updateInfo.asStateFlow()

    private val _isCheckingUpdate = MutableStateFlow(false)
    val isCheckingUpdate: StateFlow<Boolean> = _isCheckingUpdate.asStateFlow()

    fun checkForUpdates(currentVersion: String = "2.2.0") {
        viewModelScope.launch {
            _isCheckingUpdate.value = true
            try {
                val info = UpdateChecker.checkForUpdates(currentVersion)
                _updateInfo.value = info
            } catch (_: Exception) {
            } finally {
                _isCheckingUpdate.value = false
            }
        }
    }

    fun dismissUpdate() {
        _updateInfo.value = null
    }

    // -------------------------------------------------------------------------
    // GESTIÓN DE ARCHIVOS
    // -------------------------------------------------------------------------

    fun addFiles(context: Context, uris: List<Uri>) {
        val current = _selectedFiles.value.toMutableList()
        uris.forEach { uri ->
            if (current.none { it.uri == uri }) {
                current.add(PdfEngine.getFileDetails(context, uri))
            }
        }
        _selectedFiles.value = current
    }

    fun setSingleFile(context: Context, uri: Uri, loadThumbnails: Boolean = false) {
        val details = PdfEngine.getFileDetails(context, uri)
        _singleFile.value = details

        if (loadThumbnails) {
            viewModelScope.launch {
                _isLoading.value = true
                _loadingMessage.value = "Generando miniaturas de páginas..."
                try {
                    val pages = PdfEngine.renderThumbnails(context, uri)
                    _pdfPages.value = pages
                } catch (e: Exception) {
                    _result.value = OperationResult.Error("Error al cargar miniaturas: ${e.localizedMessage}", e)
                } finally {
                    _isLoading.value = false
                }
            }
        }
    }

    fun removeFile(item: DocumentFileItem) {
        _selectedFiles.value = _selectedFiles.value.filter { it.uri != item.uri }
    }

    fun moveFileUp(index: Int) {
        if (index > 0) {
            val list = _selectedFiles.value.toMutableList()
            val item = list.removeAt(index)
            list.add(index - 1, item)
            _selectedFiles.value = list
        }
    }

    fun moveFileDown(index: Int) {
        if (index < _selectedFiles.value.size - 1) {
            val list = _selectedFiles.value.toMutableList()
            val item = list.removeAt(index)
            list.add(index + 1, item)
            _selectedFiles.value = list
        }
    }

    fun clearState() {
        _selectedFiles.value = emptyList()
        _singleFile.value = null
        _pdfPages.value = emptyList()
        _extractedText.value = ""
        _result.value = null
    }

    fun clearResult() {
        _result.value = null
    }

    // -------------------------------------------------------------------------
    // OPERACIONES
    // -------------------------------------------------------------------------

    fun merge(context: Context, outputStream: OutputStream) {
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Combinando archivos PDF..."
            try {
                val uris = _selectedFiles.value.map { it.uri }
                PdfEngine.mergePdfs(context, uris, outputStream)
                _result.value = OperationResult.Success("¡Archivos PDF unidos correctamente!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al unir PDFs: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun split(context: Context, rangeStr: String, outputStream: OutputStream) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Extrayendo páginas del PDF..."
            try {
                PdfEngine.splitPdfByRanges(context, file.uri, rangeStr, outputStream)
                _result.value = OperationResult.Success("¡Páginas extraídas y guardadas con éxito!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al dividir PDF: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun rotatePageClockwise(index: Int) {
        val list = _pdfPages.value.toMutableList()
        list[index] = list[index].copy().apply { rotateClockwise() }
        _pdfPages.value = list
    }

    fun toggleDeletePage(index: Int) {
        val list = _pdfPages.value.toMutableList()
        list[index] = list[index].copy(isMarkedForDeletion = !list[index].isMarkedForDeletion)
        _pdfPages.value = list
    }

    fun exportRearranged(context: Context, outputStream: OutputStream) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Guardando documento organizado..."
            try {
                PdfEngine.exportRearrangedPdf(context, file.uri, _pdfPages.value, outputStream)
                _result.value = OperationResult.Success("¡Documento reorganizado con éxito!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al guardar páginas: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun imagesToPdf(context: Context, outputStream: OutputStream) {
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Compilando imágenes a PDF..."
            try {
                val uris = _selectedFiles.value.map { it.uri }
                PdfEngine.imagesToPdf(context, uris, outputStream)
                _result.value = OperationResult.Success("¡Imágenes convertidas a PDF con éxito!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al convertir imágenes: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun protect(context: Context, pass: String, algo: EncryptionAlgorithm, outputStream: OutputStream) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Cifrando documento con ${algo.displayName}..."
            try {
                PdfEngine.protectPdf(context, file.uri, pass, algo, outputStream)
                _result.value = OperationResult.Success("¡PDF cifrado exitosamente!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al proteger PDF: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun unlock(context: Context, pass: String, outputStream: OutputStream) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Removiendo protección del documento..."
            try {
                PdfEngine.unlockPdf(context, file.uri, pass, outputStream)
                _result.value = OperationResult.Success("¡PDF desbloqueado exitosamente!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al desbloquear: Contraseña incorrecta o error de lectura.", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun compress(context: Context, outputStream: OutputStream) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Optimizando y comprimiendo PDF..."
            try {
                PdfEngine.compressPdf(context, file.uri, outputStream)
                _result.value = OperationResult.Success("¡PDF comprimido y optimizado con éxito!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al comprimir: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    // -------------------------------------------------------------------------
    // NUEVAS OPERACIONES V2.2
    // -------------------------------------------------------------------------

    fun pdfToImages(
        context: Context,
        format: ImageExportFormat,
        scale: Float,
        outputStream: OutputStream
    ) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Exportando páginas a imágenes (${format.extension.uppercase()})..."
            try {
                PdfEngine.pdfToImages(context, file.uri, format, scale, outputStream)
                val msg = if (file.pageCount == 1) "¡Imagen exportada con éxito!" else "¡Archivo ZIP con todas las imágenes generado con éxito!"
                _result.value = OperationResult.Success(msg)
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al exportar imágenes: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun addWatermark(
        context: Context,
        text: String,
        imageUri: Uri? = null,
        opacity: Float = 0.35f,
        angleDegrees: Float = 45f,
        fontSize: Float = 48f,
        colorRgb: Triple<Float, Float, Float> = Triple(0.5f, 0.5f, 0.5f),
        position: WatermarkPosition = WatermarkPosition.DIAGONAL,
        outputStream: OutputStream
    ) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Aplicando marca de agua al documento..."
            try {
                PdfEngine.addWatermark(context, file.uri, text, imageUri, opacity, angleDegrees, fontSize, colorRgb, position, outputStream)
                _result.value = OperationResult.Success("¡Marca de agua aplicada exitosamente!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al aplicar marca de agua: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun addPageNumbers(
        context: Context,
        format: PageNumberFormat,
        position: PageNumberPosition,
        fontSize: Float = 11f,
        skipCover: Boolean = true,
        outputStream: OutputStream
    ) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Estampando numeración de páginas..."
            try {
                PdfEngine.addPageNumbers(context, file.uri, format, position, fontSize, skipCover, outputStream)
                _result.value = OperationResult.Success("¡Numeración de páginas agregada exitosamente!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al numerar páginas: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun rotateBulk(
        context: Context,
        degrees: Int,
        filter: RotateFilter,
        outputStream: OutputStream
    ) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Rotando páginas seleccionadas ($degrees°)..."
            try {
                PdfEngine.rotateBulk(context, file.uri, degrees, filter, outputStream)
                _result.value = OperationResult.Success("¡Páginas rotadas exitosamente!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al rotar en bloque: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun extractText(context: Context) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Extrayendo contenido de texto del PDF..."
            try {
                val text = PdfEngine.extractText(context, file.uri)
                _extractedText.value = text
                if (text.isBlank()) {
                    _result.value = OperationResult.Success("Extracción completada: El documento no contiene texto indexable (podría ser un escaneo de imagen).")
                } else {
                    _result.value = OperationResult.Success("¡Texto extraído con éxito!", extraData = text)
                }
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al extraer texto: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun saveExtractedText(text: String, outputStream: OutputStream) {
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Guardando archivo de texto plano..."
            try {
                PdfEngine.saveTextToFile(text, outputStream)
                _result.value = OperationResult.Success("¡Archivo .txt guardado correctamente!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al guardar texto: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun cropMargins(
        context: Context,
        topMm: Float,
        bottomMm: Float,
        leftMm: Float,
        rightMm: Float,
        outputStream: OutputStream
    ) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Recortando márgenes del documento..."
            try {
                PdfEngine.cropMargins(context, file.uri, topMm, bottomMm, leftMm, rightMm, outputStream)
                _result.value = OperationResult.Success("¡Márgenes recortados exitosamente!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al recortar márgenes: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun stampSignature(
        context: Context,
        pageIndex: Int,
        signatureBitmap: Bitmap,
        posXRatio: Float = 0.60f,
        posYRatio: Float = 0.08f,
        targetWidthRatio: Float = 0.32f,
        outputStream: OutputStream
    ) {
        val file = _singleFile.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            _loadingMessage.value = "Estampando firma digital en la página..."
            try {
                PdfEngine.stampSignature(context, file.uri, pageIndex, signatureBitmap, posXRatio, posYRatio, targetWidthRatio, outputStream)
                _result.value = OperationResult.Success("¡Documento firmado exitosamente!")
            } catch (e: Exception) {
                _result.value = OperationResult.Error("Error al estampar firma: ${e.localizedMessage}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }
}

