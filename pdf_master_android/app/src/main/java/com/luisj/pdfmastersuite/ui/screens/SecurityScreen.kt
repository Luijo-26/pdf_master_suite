package com.luisj.pdfmastersuite.ui.screens

import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.luisj.pdfmastersuite.core.models.EncryptionAlgorithm
import com.luisj.pdfmastersuite.core.models.OperationResult
import com.luisj.pdfmastersuite.ui.components.*
import com.luisj.pdfmastersuite.ui.theme.*
import com.luisj.pdfmastersuite.ui.viewmodel.PdfToolViewModel

@Composable
fun SecurityScreen(
    viewModel: PdfToolViewModel,
    onNavigateBack: () -> Unit
) {
    val context = LocalContext.current
    val singleFile by viewModel.singleFile.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val loadingMsg by viewModel.loadingMessage.collectAsState()
    val result by viewModel.result.collectAsState()

    var selectedTab by remember { mutableIntStateOf(0) } // 0 = Proteger, 1 = Desbloquear
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    var selectedAlgorithm by remember { mutableStateOf(EncryptionAlgorithm.AES_256) }

    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri: Uri? ->
        if (uri != null) {
            viewModel.setSingleFile(context, uri)
            password = ""
        }
    }

    val saveFileLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument("application/pdf")
    ) { outputUri: Uri? ->
        if (outputUri != null) {
            context.contentResolver.openOutputStream(outputUri)?.let { stream ->
                if (selectedTab == 0) {
                    viewModel.protect(context, password, selectedAlgorithm, stream)
                } else {
                    viewModel.unlock(context, password, stream)
                }
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
                title = "Seguridad de PDF",
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
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Selector de pestañas
                TabRow(
                    selectedTabIndex = selectedTab,
                    containerColor = SurfaceDark,
                    contentColor = PrimaryIndigo
                ) {
                    Tab(
                        selected = selectedTab == 0,
                        onClick = { selectedTab = 0 },
                        text = { Text("Proteger con Clave") }
                    )
                    Tab(
                        selected = selectedTab == 1,
                        onClick = { selectedTab = 1 },
                        text = { Text("Desbloquear PDF") }
                    )
                }

                if (singleFile == null) {
                    FilePickerZone(
                        title = "Seleccionar PDF",
                        subtitle = "Elige el archivo para ${if (selectedTab == 0) "cifrar" else "desbloquear"}",
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
                                text = "${file.sizeFormatted} • ${if (file.isEncrypted) "Protegido actualmente" else "Sin cifrado"}",
                                style = MaterialTheme.typography.bodySmall,
                                color = TextSecondary
                            )
                            Spacer(modifier = Modifier.height(10.dp))
                            OutlinedButton(onClick = { filePicker.launch(arrayOf("application/pdf")) }) {
                                Text("Cambiar archivo")
                            }
                        }
                    }

                    // Campo de contraseña
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(12.dp)),
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = if (selectedTab == 0) "Establecer contraseña" else "Ingresa la contraseña actual",
                                style = MaterialTheme.typography.titleSmall,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(12.dp))

                            OutlinedTextField(
                                value = password,
                                onValueChange = { password = it },
                                modifier = Modifier.fillMaxWidth(),
                                singleLine = true,
                                visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                                trailingIcon = {
                                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                                        Icon(
                                            imageVector = if (passwordVisible) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                                            contentDescription = null,
                                            tint = TextSecondary
                                        )
                                    }
                                },
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedBorderColor = PrimaryIndigo,
                                    unfocusedBorderColor = BorderDark,
                                    focusedTextColor = TextPrimary,
                                    unfocusedTextColor = TextPrimary
                                )
                            )

                            if (selectedTab == 0 && password.isNotBlank()) {
                                Spacer(modifier = Modifier.height(8.dp))
                                val strength = if (password.length >= 10) "Fuerte" else if (password.length >= 6) "Media" else "Débil"
                                val color = if (password.length >= 10) AccentGreen else if (password.length >= 6) AccentAmber else AccentRed
                                Text(
                                    text = "Fortaleza: $strength",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = color
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.weight(1f))

                    Button(
                        onClick = {
                            val defaultName = if (selectedTab == 0) "PDF_Protegido.pdf" else "PDF_Desbloqueado.pdf"
                            saveFileLauncher.launch(defaultName)
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (selectedTab == 0) PrimaryIndigo else AccentGreen
                        ),
                        enabled = password.isNotBlank()
                    ) {
                        Icon(
                            imageVector = if (selectedTab == 0) Icons.Default.Lock else Icons.Default.LockOpen,
                            contentDescription = null
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = if (selectedTab == 0) "Cifrar Documento" else "Desbloquear Documento",
                            style = MaterialTheme.typography.titleMedium
                        )
                    }
                }
            }

            if (isLoading) {
                ProcessingDialog(message = loadingMsg)
            }
        }
    }
}
