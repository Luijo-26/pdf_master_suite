package com.luisj.pdfmastersuite.ui.screens

import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Crop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.luisj.pdfmastersuite.core.models.OperationResult
import com.luisj.pdfmastersuite.ui.components.*
import com.luisj.pdfmastersuite.ui.theme.*
import com.luisj.pdfmastersuite.ui.viewmodel.PdfToolViewModel

@Composable
fun CropScreen(
    viewModel: PdfToolViewModel,
    onNavigateBack: () -> Unit
) {
    val context = LocalContext.current
    val singleFile by viewModel.singleFile.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val loadingMsg by viewModel.loadingMessage.collectAsState()
    val result by viewModel.result.collectAsState()

    var topMm by remember { mutableFloatStateOf(10f) }
    var bottomMm by remember { mutableFloatStateOf(10f) }
    var leftMm by remember { mutableFloatStateOf(10f) }
    var rightMm by remember { mutableFloatStateOf(10f) }

    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri: Uri? ->
        if (uri != null) {
            viewModel.setSingleFile(context, uri)
        }
    }

    val saveFileLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument("application/pdf")
    ) { outputUri: Uri? ->
        if (outputUri != null) {
            context.contentResolver.openOutputStream(outputUri)?.let { stream ->
                viewModel.cropMargins(context, topMm, bottomMm, leftMm, rightMm, stream)
            }
        }
    }

    LaunchedEffect(result) {
        when (val res = result) {
            is OperationResult.Success -> {
                Toast.makeText(context, res.message, Toast.LENGTH_LONG).show()
                viewModel.clearResult()
            }
            is OperationResult.Error -> {
                Toast.makeText(context, res.message, Toast.LENGTH_LONG).show()
                viewModel.clearResult()
            }
            null -> {}
        }
    }

    Scaffold(
        containerColor = BgDark,
        topBar = {
            AppTopBar(
                title = "Recortar PDF",
                canNavigateBack = true,
                onNavigateBack = {
                    viewModel.clearState()
                    onNavigateBack()
                }
            )
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                if (singleFile == null) {
                    FilePickerZone(
                        title = "Seleccionar PDF para Recortar",
                        subtitle = "Ajusta márgenes exteriores para eliminar bordes blancos o imprimir",
                        onClick = { filePicker.launch(arrayOf("application/pdf")) }
                    )
                } else {
                    val file = singleFile!!
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceCard)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = file.name,
                                style = MaterialTheme.typography.titleMedium,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "${file.sizeFormatted} • ${file.pageCount ?: "?"} páginas",
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextSecondary
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            OutlinedButton(onClick = { filePicker.launch(arrayOf("application/pdf")) }) {
                                Text("Cambiar archivo")
                            }
                        }
                    }

                    // Preajustes rápidos
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Preajustes Rápidos de Margen",
                                style = MaterialTheme.typography.titleSmall,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(10.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                FilterChip(
                                    selected = topMm == 5f && bottomMm == 5f && leftMm == 5f && rightMm == 5f,
                                    onClick = {
                                        topMm = 5f; bottomMm = 5f; leftMm = 5f; rightMm = 5f
                                    },
                                    label = { Text("Sutil (5 mm)") }
                                )
                                FilterChip(
                                    selected = topMm == 10f && bottomMm == 10f && leftMm == 10f && rightMm == 10f,
                                    onClick = {
                                        topMm = 10f; bottomMm = 10f; leftMm = 10f; rightMm = 10f
                                    },
                                    label = { Text("Estándar (10 mm)") }
                                )
                                FilterChip(
                                    selected = topMm == 20f && bottomMm == 20f && leftMm == 20f && rightMm == 20f,
                                    onClick = {
                                        topMm = 20f; bottomMm = 20f; leftMm = 20f; rightMm = 20f
                                    },
                                    label = { Text("Amplio (20 mm)") }
                                )
                            }
                        }
                    }

                    // Deslizadores independientes
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Ajuste Personalizado (mm)",
                                style = MaterialTheme.typography.titleSmall,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(10.dp))

                            Text("Superior: ${topMm.toInt()} mm", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                            Slider(value = topMm, onValueChange = { topMm = it }, valueRange = 0f..40f)

                            Text("Inferior: ${bottomMm.toInt()} mm", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                            Slider(value = bottomMm, onValueChange = { bottomMm = it }, valueRange = 0f..40f)

                            Text("Izquierdo: ${leftMm.toInt()} mm", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                            Slider(value = leftMm, onValueChange = { leftMm = it }, valueRange = 0f..40f)

                            Text("Derecho: ${rightMm.toInt()} mm", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                            Slider(value = rightMm, onValueChange = { rightMm = it }, valueRange = 0f..40f)
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Button(
                        onClick = { saveFileLauncher.launch("PDF_Recortado.pdf") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AccentPurple)
                    ) {
                        Icon(imageVector = Icons.Default.Crop, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Recortar y Guardar", style = MaterialTheme.typography.titleMedium)
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                }
            }

            if (isLoading) {
                ProcessingDialog(message = loadingMsg)
            }
        }
    }
}
