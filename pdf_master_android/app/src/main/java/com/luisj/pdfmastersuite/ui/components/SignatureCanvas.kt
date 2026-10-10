package com.luisj.pdfmastersuite.ui.components

import android.graphics.Bitmap
import android.graphics.Paint
import android.graphics.Path
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asAndroidPath
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import com.luisj.pdfmastersuite.ui.theme.*

data class SignaturePath(
    val path: androidx.compose.ui.graphics.Path,
    val color: Color,
    val strokeWidth: Float
)

@Composable
fun SignatureCanvas(
    modifier: Modifier = Modifier,
    onSignatureCaptured: (Bitmap?) -> Unit
) {
    val paths = remember { mutableStateListOf<SignaturePath>() }
    var currentPath by remember { mutableStateOf<androidx.compose.ui.graphics.Path?>(null) }
    var selectedColor by remember { mutableStateOf(Color(0xFF1E3A8A)) } // Azul ejecutivo clásico
    var strokeWidth by remember { mutableFloatStateOf(6f) }
    var canvasSize by remember { mutableStateOf(IntSize.Zero) }

    fun generateBitmap(): Bitmap? {
        if (canvasSize.width <= 0 || canvasSize.height <= 0 || paths.isEmpty()) return null
        val bitmap = Bitmap.createBitmap(canvasSize.width, canvasSize.height, Bitmap.Config.ARGB_8888)
        val canvas = android.graphics.Canvas(bitmap)

        paths.forEach { item ->
            val paint = Paint().apply {
                color = item.color.toArgb()
                style = Paint.Style.STROKE
                strokeCap = Paint.Cap.ROUND
                strokeJoin = Paint.Join.ROUND
                isAntiAlias = true
                this.strokeWidth = item.strokeWidth
            }
            canvas.drawPath(item.path.asAndroidPath(), paint)
        }
        return bitmap
    }

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Lienzo táctil
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(200.dp)
                .clip(RoundedCornerShape(16.dp))
                .background(Color.White)
                .border(1.5.dp, BorderDark, RoundedCornerShape(16.dp))
                .onSizeChanged { canvasSize = it }
        ) {
            Canvas(
                modifier = Modifier
                    .fillMaxSize()
                    .pointerInput(selectedColor, strokeWidth) {
                        detectDragGestures(
                            onDragStart = { offset ->
                                val p = androidx.compose.ui.graphics.Path().apply {
                                    moveTo(offset.x, offset.y)
                                }
                                currentPath = p
                            },
                            onDrag = { change, _ ->
                                currentPath?.lineTo(change.position.x, change.position.y)
                                // Trigger recomposition
                                currentPath = currentPath
                            },
                            onDragEnd = {
                                currentPath?.let {
                                    paths.add(SignaturePath(it, selectedColor, strokeWidth))
                                    currentPath = null
                                    onSignatureCaptured(generateBitmap())
                                }
                            },
                            onDragCancel = {
                                currentPath = null
                            }
                        )
                    }
            ) {
                // Dibujar línea guía de base
                val lineY = size.height * 0.75f
                drawLine(
                    color = Color.LightGray.copy(alpha = 0.6f),
                    start = Offset(40f, lineY),
                    end = Offset(size.width - 40f, lineY),
                    strokeWidth = 2f
                )

                // Dibujar trazos existentes
                paths.forEach { item ->
                    drawPath(
                        path = item.path,
                        color = item.color,
                        style = Stroke(
                            width = item.strokeWidth,
                            cap = androidx.compose.ui.graphics.StrokeCap.Round,
                            join = androidx.compose.ui.graphics.StrokeJoin.Round
                        )
                    )
                }

                // Dibujar trazo en curso
                currentPath?.let {
                    drawPath(
                        path = it,
                        color = selectedColor,
                        style = Stroke(
                            width = strokeWidth,
                            cap = androidx.compose.ui.graphics.StrokeCap.Round,
                            join = androidx.compose.ui.graphics.StrokeJoin.Round
                        )
                    )
                }
            }

            if (paths.isEmpty() && currentPath == null) {
                Text(
                    text = "Firma aquí con el dedo o stylus",
                    color = Color.Gray.copy(alpha = 0.7f),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.align(Alignment.Center)
                )
            }
        }

        // Barra de herramientas: Colores, Grosores y Limpiar
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Colores de tinta
            Row(
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                val colors = listOf(
                    Color(0xFF1E3A8A) to "Azul",
                    Color(0xFF111827) to "Negro"
                )
                colors.forEach { (c, _) ->
                    Box(
                        modifier = Modifier
                            .size(32.dp)
                            .clip(CircleShape)
                            .background(c)
                            .border(
                                width = if (selectedColor == c) 2.5.dp else 1.dp,
                                color = if (selectedColor == c) AccentCyan else BorderDark,
                                shape = CircleShape
                            )
                            .clickable { selectedColor = c }
                    )
                }

                Spacer(modifier = Modifier.width(8.dp))

                // Selector de grosor
                FilterChip(
                    selected = strokeWidth == 4f,
                    onClick = { strokeWidth = 4f },
                    label = { Text("Fino", style = MaterialTheme.typography.labelSmall) }
                )
                FilterChip(
                    selected = strokeWidth == 7f,
                    onClick = { strokeWidth = 7f },
                    label = { Text("Medio", style = MaterialTheme.typography.labelSmall) }
                )
            }

            // Botón Limpiar
            IconButton(
                onClick = {
                    paths.clear()
                    currentPath = null
                    onSignatureCaptured(null)
                },
                enabled = paths.isNotEmpty()
            ) {
                Icon(
                    imageVector = Icons.Default.Delete,
                    contentDescription = "Limpiar firma",
                    tint = if (paths.isNotEmpty()) AccentRed else TextMuted
                )
            }
        }
    }
}
