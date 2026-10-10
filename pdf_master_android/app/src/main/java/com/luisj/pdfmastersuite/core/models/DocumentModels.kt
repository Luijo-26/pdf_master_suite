package com.luisj.pdfmastersuite.core.models

import android.graphics.Bitmap
import android.net.Uri

/**
 * Representa un archivo cargado en la aplicación (PDF o Imagen).
 */
data class DocumentFileItem(
    val uri: Uri,
    val name: String,
    val sizeBytes: Long = 0L,
    val pageCount: Int? = null,
    val isEncrypted: Boolean = false
) {
    val sizeFormatted: String
        get() {
            if (sizeBytes <= 0) return "0 KB"
            val kb = sizeBytes / 1024.0
            return if (kb < 1024) {
                String.format("%.1f KB", kb)
            } else {
                String.format("%.2f MB", kb / 1024.0)
            }
        }
}

/**
 * Representa una página individual de un PDF para organizar, rotar o eliminar.
 */
data class PdfPageItem(
    val originalPageIndex: Int, // 0-indexado
    val displayPageNumber: Int, // 1-indexado para mostrar al usuario
    var rotationDegrees: Int = 0, // 0, 90, 180, 270
    var thumbnail: Bitmap? = null,
    var isMarkedForDeletion: Boolean = false
) {
    fun rotateClockwise() {
        rotationDegrees = (rotationDegrees + 90) % 360
    }

    fun rotateCounterClockwise() {
        rotationDegrees = (rotationDegrees - 90 + 360) % 360
    }
}

/**
 * Modos de división de PDF.
 */
enum class SplitMode {
    BY_RANGES,
    ALL_PAGES
}

/**
 * Algoritmo de cifrado para protección.
 */
enum class EncryptionAlgorithm(val keyLength: Int, val displayName: String) {
    AES_256(256, "AES-256 (Máxima seguridad)"),
    AES_128(128, "AES-128 (Estándar)")
}

/**
 * Posición para marca de agua.
 */
enum class WatermarkPosition(val displayName: String) {
    CENTER("Centro"),
    DIAGONAL("Diagonal (45°)"),
    TOP_CENTER("Superior Centrado"),
    BOTTOM_CENTER("Inferior Centrado")
}

/**
 * Formato para numeración de páginas.
 */
enum class PageNumberFormat(val displayName: String) {
    PAG_X("Pág. X"),
    X_DE_Y("X de Y"),
    DASHES("- X -"),
    ONLY_X("X")
}

/**
 * Posición para numeración de páginas.
 */
enum class PageNumberPosition(val displayName: String) {
    BOTTOM_CENTER("Inferior Centro"),
    BOTTOM_RIGHT("Inferior Derecha"),
    BOTTOM_LEFT("Inferior Izquierda"),
    TOP_CENTER("Superior Centro"),
    TOP_RIGHT("Superior Derecha")
}

/**
 * Filtro de páginas para rotación en bloque.
 */
enum class RotateFilter(val displayName: String) {
    ALL("Todas las páginas"),
    EVEN("Solo páginas pares"),
    ODD("Solo páginas impares")
}

/**
 * Resolución/Calidad para exportar PDF a Imágenes.
 */
enum class ImageExportFormat(val extension: String, val mimeType: String) {
    PNG("png", "image/png"),
    JPEG("jpg", "image/jpeg")
}

/**
 * Resultado de una operación del motor PDF.
 */
sealed class OperationResult {
    data class Success(val message: String, val outputUri: Uri? = null, val extraData: String? = null) : OperationResult()
    data class Error(val message: String, val exception: Throwable? = null) : OperationResult()
}

