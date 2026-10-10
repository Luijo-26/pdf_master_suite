package com.luisj.pdfmastersuite.ui.screens

import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.CallSplit
import androidx.compose.material.icons.automirrored.filled.MergeType
import androidx.compose.material.icons.automirrored.filled.RotateRight
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.luisj.pdfmastersuite.ui.components.ToolCard
import com.luisj.pdfmastersuite.ui.theme.*
import com.luisj.pdfmastersuite.ui.viewmodel.PdfToolViewModel

private enum class ToolCategory(val title: String) {
    ALL("Todos"),
    ORGANIZE("Organizar"),
    EDIT("Editar"),
    CONVERT("Convertir"),
    SECURITY("Seguridad")
}

private data class ToolItem(
    val id: String,
    val title: String,
    val description: String,
    val icon: ImageVector,
    val iconColor: Color,
    val category: ToolCategory,
    val badgeText: String? = null,
    val onClick: () -> Unit
)

@Composable
fun HomeScreen(
    viewModel: PdfToolViewModel,
    onNavigateToMerge: () -> Unit,
    onNavigateToSplit: () -> Unit,
    onNavigateToOrganize: () -> Unit,
    onNavigateToImagesToPdf: () -> Unit,
    onNavigateToCompress: () -> Unit,
    onNavigateToSecurity: () -> Unit,
    onNavigateToPdfToImages: () -> Unit,
    onNavigateToWatermark: () -> Unit,
    onNavigateToPageNumbers: () -> Unit,
    onNavigateToRotateBulk: () -> Unit,
    onNavigateToPdfToText: () -> Unit,
    onNavigateToCrop: () -> Unit,
    onNavigateToSign: () -> Unit
) {
    val context = LocalContext.current
    val updateInfo by viewModel.updateInfo.collectAsState()
    val isCheckingUpdate by viewModel.isCheckingUpdate.collectAsState()

    var searchQuery by remember { mutableStateOf("") }
    var selectedCategory by remember { mutableStateOf(ToolCategory.ALL) }

    val allTools = remember(
        onNavigateToMerge, onNavigateToSplit, onNavigateToOrganize,
        onNavigateToImagesToPdf, onNavigateToCompress, onNavigateToSecurity,
        onNavigateToPdfToImages, onNavigateToWatermark, onNavigateToPageNumbers,
        onNavigateToRotateBulk, onNavigateToPdfToText, onNavigateToCrop, onNavigateToSign
    ) {
        listOf(
            // ORGANIZAR
            ToolItem(
                id = "merge",
                title = "Unir PDFs",
                description = "Combina múltiples archivos PDF en el orden exacto que prefieras.",
                icon = Icons.AutoMirrored.Filled.MergeType,
                iconColor = PrimaryIndigo,
                category = ToolCategory.ORGANIZE,
                badgeText = "Popular",
                onClick = onNavigateToMerge
            ),
            ToolItem(
                id = "split",
                title = "Dividir PDF",
                description = "Extrae páginas individuales o por rangos numéricos como 1-3, 5.",
                icon = Icons.AutoMirrored.Filled.CallSplit,
                iconColor = AccentCyan,
                category = ToolCategory.ORGANIZE,
                onClick = onNavigateToSplit
            ),
            ToolItem(
                id = "organize",
                title = "Organizar Páginas",
                description = "Reordena visualmente con miniaturas, rota y elimina páginas.",
                icon = Icons.Default.GridView,
                iconColor = AccentPurple,
                category = ToolCategory.ORGANIZE,
                badgeText = "Visual",
                onClick = onNavigateToOrganize
            ),
            ToolItem(
                id = "rotate_bulk",
                title = "Rotar en Bloque",
                description = "Gira todas las páginas o solo pares/impares a 90°, 180° o 270°.",
                icon = Icons.AutoMirrored.Filled.RotateRight,
                iconColor = PrimaryIndigo,
                category = ToolCategory.ORGANIZE,
                badgeText = "Nuevo",
                onClick = onNavigateToRotateBulk
            ),

            // EDITAR
            ToolItem(
                id = "sign",
                title = "Firmar PDF",
                description = "Dibuja tu firma táctil en el lienzo e insértala en cualquier página.",
                icon = Icons.Default.Draw,
                iconColor = AccentCyan,
                category = ToolCategory.EDIT,
                badgeText = "Táctil",
                onClick = onNavigateToSign
            ),
            ToolItem(
                id = "watermark",
                title = "Marca de Agua",
                description = "Inserta texto o logos personalizados con opacidad y rotación.",
                icon = Icons.Default.BrandingWatermark,
                iconColor = AccentPurple,
                category = ToolCategory.EDIT,
                badgeText = "Nuevo",
                onClick = onNavigateToWatermark
            ),
            ToolItem(
                id = "page_numbers",
                title = "Numerar Páginas",
                description = "Agrega números de página 'Pág. X de Y' con opción de omitir portada.",
                icon = Icons.Default.FormatListNumbered,
                iconColor = AccentCyan,
                category = ToolCategory.EDIT,
                badgeText = "Nuevo",
                onClick = onNavigateToPageNumbers
            ),
            ToolItem(
                id = "crop",
                title = "Recortar PDF",
                description = "Ajusta márgenes exteriores para eliminar bordes blancos innecesarios.",
                icon = Icons.Default.Crop,
                iconColor = AccentPurple,
                category = ToolCategory.EDIT,
                badgeText = "Nuevo",
                onClick = onNavigateToCrop
            ),

            // CONVERTIR
            ToolItem(
                id = "images_to_pdf",
                title = "Imágenes a PDF",
                description = "Convierte fotos JPG, PNG o WEBP en un único documento limpio.",
                icon = Icons.Default.Image,
                iconColor = AccentGreen,
                category = ToolCategory.CONVERT,
                badgeText = "Popular",
                onClick = onNavigateToImagesToPdf
            ),
            ToolItem(
                id = "pdf_to_images",
                title = "PDF a Imágenes",
                description = "Exporta cada página a JPG o PNG de alta fidelidad o archivo ZIP.",
                icon = Icons.Default.Collections,
                iconColor = AccentGreen,
                category = ToolCategory.CONVERT,
                badgeText = "Nuevo",
                onClick = onNavigateToPdfToImages
            ),
            ToolItem(
                id = "pdf_to_text",
                title = "PDF a Texto (.txt)",
                description = "Extrae todo el contenido indexable con recuento de palabras.",
                icon = Icons.Default.TextFields,
                iconColor = AccentAmber,
                category = ToolCategory.CONVERT,
                badgeText = "Nuevo",
                onClick = onNavigateToPdfToText
            ),

            // SEGURIDAD & COMPRESIÓN
            ToolItem(
                id = "compress",
                title = "Comprimir PDF",
                description = "Reduce el tamaño optimizando objetos redundantes y flujos.",
                icon = Icons.Default.Compress,
                iconColor = AccentAmber,
                category = ToolCategory.SECURITY,
                onClick = onNavigateToCompress
            ),
            ToolItem(
                id = "security",
                title = "Seguridad (Cifrar / Quitar)",
                description = "Protege con clave bancaria AES-256 o remueve la contraseña existente.",
                icon = Icons.Default.Lock,
                iconColor = AccentRed,
                category = ToolCategory.SECURITY,
                onClick = onNavigateToSecurity
            )
        )
    }

    // Filtrado reactivo en tiempo real por búsqueda y categoría
    val filteredTools = remember(searchQuery, selectedCategory, allTools) {
        allTools.filter { tool ->
            val matchesCategory = (selectedCategory == ToolCategory.ALL) || (tool.category == selectedCategory)
            val matchesSearch = searchQuery.isBlank() ||
                    tool.title.contains(searchQuery, ignoreCase = true) ||
                    tool.description.contains(searchQuery, ignoreCase = true)
            matchesCategory && matchesSearch
        }
    }

    Scaffold(
        containerColor = BgDark
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            item {
                Spacer(modifier = Modifier.height(16.dp))

                // Encabezado Premium
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(46.dp)
                                .clip(RoundedCornerShape(14.dp))
                                .background(PrimaryIndigo),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.PictureAsPdf,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(26.dp)
                            )
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = "PDF Master Suite",
                                    style = MaterialTheme.typography.titleLarge,
                                    fontWeight = FontWeight.Bold,
                                    color = TextPrimary
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Surface(
                                    shape = RoundedCornerShape(6.dp),
                                    color = AccentCyan.copy(alpha = 0.18f)
                                ) {
                                    Text(
                                        text = "v2.2",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = AccentCyan,
                                        fontWeight = FontWeight.Bold,
                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                    )
                                }
                            }
                            Text(
                                text = "13 herramientas locales estilo iLovePDF",
                                style = MaterialTheme.typography.bodySmall,
                                color = TextSecondary
                            )
                        }
                    }

                    // Botón para comprobar actualizaciones
                    IconButton(
                        onClick = {
                            Toast.makeText(context, "Comprobando actualizaciones...", Toast.LENGTH_SHORT).show()
                            viewModel.checkForUpdates("2.2.0")
                        }
                    ) {
                        if (isCheckingUpdate) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(20.dp),
                                strokeWidth = 2.dp,
                                color = AccentCyan
                            )
                        } else {
                            Icon(
                                imageVector = Icons.Default.Sync,
                                contentDescription = "Buscar actualizaciones",
                                tint = TextSecondary
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Banner interactivo de actualización disponible
                if (updateInfo != null) {
                    val info = updateInfo!!
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.5.dp, AccentCyan.copy(alpha = 0.6f), RoundedCornerShape(14.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(38.dp)
                                        .clip(RoundedCornerShape(10.dp))
                                        .background(AccentCyan.copy(alpha = 0.15f)),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.SystemUpdate,
                                        contentDescription = null,
                                        tint = AccentCyan,
                                        modifier = Modifier.size(22.dp)
                                    )
                                }
                                Spacer(modifier = Modifier.width(12.dp))
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = "¡Nueva versión disponible: v${info.latestVersion}!",
                                        style = MaterialTheme.typography.titleSmall,
                                        fontWeight = FontWeight.Bold,
                                        color = TextPrimary
                                    )
                                    Text(
                                        text = "Hay una actualización disponible en GitHub con mejoras.",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = TextSecondary
                                    )
                                }
                            }
                            Spacer(modifier = Modifier.height(12.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.End,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                TextButton(onClick = { viewModel.dismissUpdate() }) {
                                    Text("Ignorar", color = TextSecondary)
                                }
                                Spacer(modifier = Modifier.width(8.dp))
                                Button(
                                    onClick = {
                                        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(info.downloadUrl))
                                        context.startActivity(intent)
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = AccentCyan),
                                    shape = RoundedCornerShape(8.dp)
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Download,
                                        contentDescription = null,
                                        modifier = Modifier.size(16.dp),
                                        tint = Color.Black
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(
                                        text = "Descargar",
                                        color = Color.Black,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }
                        }
                    }
                    Spacer(modifier = Modifier.height(14.dp))
                }

                // Banner de privacidad y seguridad local
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = SurfaceDark,
                    border = androidx.compose.foundation.BorderStroke(1.dp, BorderDark)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.Shield,
                            contentDescription = null,
                            tint = AccentGreen,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Text(
                            text = "100% Privado y local. Procesamiento en el dispositivo sin conexión externa.",
                            style = MaterialTheme.typography.bodySmall,
                            color = TextSecondary
                        )
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Barra de Búsqueda Fluida
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    placeholder = {
                        Text(
                            text = "Buscar herramienta (firmar, rotar, marca...)",
                            color = TextMuted,
                            style = MaterialTheme.typography.bodyMedium
                        )
                    },
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Default.Search,
                            contentDescription = "Buscar",
                            tint = TextSecondary
                        )
                    },
                    trailingIcon = {
                        if (searchQuery.isNotBlank()) {
                            IconButton(onClick = { searchQuery = "" }) {
                                Icon(
                                    imageVector = Icons.Default.Clear,
                                    contentDescription = "Borrar búsqueda",
                                    tint = TextSecondary
                                )
                            }
                        }
                    },
                    singleLine = true,
                    shape = RoundedCornerShape(14.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = SurfaceDark,
                        unfocusedContainerColor = SurfaceDark,
                        focusedBorderColor = PrimaryIndigo,
                        unfocusedBorderColor = BorderDark,
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(10.dp))

                // Fila de Chips de Categoría
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    ToolCategory.values().forEach { category ->
                        val count = if (category == ToolCategory.ALL) allTools.size else allTools.count { it.category == category }
                        FilterChip(
                            selected = selectedCategory == category,
                            onClick = { selectedCategory = category },
                            label = {
                                Text("${category.title} ($count)")
                            },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = PrimaryIndigo,
                                selectedLabelColor = Color.White
                            )
                        )
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))
            }

            // Lista de Tarjetas Animadas
            items(filteredTools, key = { it.id }) { tool ->
                ToolCard(
                    title = tool.title,
                    description = tool.description,
                    icon = tool.icon,
                    iconColor = tool.iconColor,
                    badgeText = tool.badgeText,
                    onClick = tool.onClick
                )
            }

            if (filteredTools.isEmpty()) {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 40.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Icon(
                                imageVector = Icons.Default.SearchOff,
                                contentDescription = null,
                                tint = TextMuted,
                                modifier = Modifier.size(48.dp)
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "No se encontraron herramientas",
                                style = MaterialTheme.typography.titleMedium,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Intenta con otro término de búsqueda o categoría",
                                style = MaterialTheme.typography.bodySmall,
                                color = TextSecondary
                            )
                        }
                    }
                }
            }

            item {
                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}
