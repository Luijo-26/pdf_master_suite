// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
}

// Redirección de la carpeta build fuera de OneDrive para prevenir bloqueos de Windows y sincronización
val baseBuildDir = File(System.getProperty("user.home"), "AndroidBuilds/pdf_master_android")
layout.buildDirectory.set(File(baseBuildDir, "root"))
subprojects {
    layout.buildDirectory.set(File(baseBuildDir, project.name))
}

