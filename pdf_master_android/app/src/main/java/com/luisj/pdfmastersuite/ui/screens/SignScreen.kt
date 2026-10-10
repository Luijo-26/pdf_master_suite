package com.luisj.pdfmastersuite.ui.screens

import android.graphics.Bitmap
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
import androidx.compose.material.icons.filled.Draw
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
fun SignScreen(
    viewModel: PdfToolViewModel,
    onNavigateBack: () -> Unit
) {
    val context = LocalContext.current
    val singleFile by viewModel.singleFile.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val loadingMsg by viewModel.loadingMessage.collectAsState()
    val result by viewModel.result.collectAsState()

    var signatureBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var targetPageIndex by remember { mutableIntStateOf(0) }
    var selectedPlacement by remember { mutableStateOf("Der") } // "Der", "Centro", "Izq"

    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri: Uri? ->
        if (uri != null) {
            viewModel.setSingleFile(context, uri)
            targetPageIndex = 0
        }
    }

    val saveFileLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument("application/pdf")
    ) { outputUri: Uri? ->
        if (outputUri != null && signatureBitmap != null) {
            context.contentResolver.openOutputStream(outputUri)?.let { stream ->
                val posXRatio = when (selectedPlacement) {
                    "Izq" -> 0.10f
                    "Centro" -> 0.35f
                    else -> 0.60f
                }
                viewModel.stampSignature(
                    context = context,
                    pageIndex = targetPageIndex,
                    signatureBitmap = signatureBitmap!!,
                    posXRatio = posXRatio,
                    posYRatio = 0.08f,
                    targetWidthRatio = 0.30f,
                    outputStream = stream
                )
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
                title = "Firmar PDF",
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
                        title = "Seleccionar PDF para Firmar",
                        subtitle = "Dibuja tu firma táctil e insértala en cualquier página del documento",
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

                    // Lienzo de Firma
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Lienzo de Firma Táctil",
                                style = MaterialTheme.typography.titleSmall,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(10.dp))
                            SignatureCanvas(
                                onSignatureCaptured = { signatureBitmap = it }
                            )
                        }
                    }

                    // Configuración de Ubicación y Página
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Ubicación en el Documento",
                                style = MaterialTheme.typography.titleSmall,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(10.dp))

                            val total = file.pageCount ?: 1
                            if (total > 1) {
                                Text(
                                    text = "Página a firmar: ${targetPageIndex + 1} de $total",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = TextSecondary
                                )
                                Slider(
                                    value = targetPageIndex.toFloat(),
                                    onValueChange = { targetPageIndex = it.toInt() },
                                    valueRange = 0f..(total - 1).toFloat(),
                                    steps = (total - 2).coerceAtLeast(0)
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                            }

                            Text(
                                text = "Posición horizontal inferior:",
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextSecondary
                            )
                            Spacer(modifier = Modifier.height(6.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(10.dp)
                            ) {
                                FilterChip(
                                    selected = selectedPlacement == "Der",
                                    onClick = { selectedPlacement = "Der" },
                                    label = { Text("Inferior Derecha") }
                                )
                                FilterChip(
                                    selected = selectedPlacement == "Centro",
                                    onClick = { selectedPlacement = "Centro" },
                                    label = { Text("Inferior Centro") }
                                )
                                FilterChip(
                                    selected = selectedPlacement == "Izq",
                                    onClick = { selectedPlacement = "Izq" },
                                    label = { Text("Inferior Izquierda") }
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Button(
                        onClick = { saveFileLauncher.launch("PDF_Firmado.pdf") },
                        enabled = signatureBitmap != null,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryIndigo)
                    ) {
                        Icon(imageVector = Icons.Default.Draw, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = if (signatureBitmap != null) "Estampar Firma y Guardar" else "Dibuja tu firma para continuar",
                            style = MaterialTheme.typography.titleMedium
                        )
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
