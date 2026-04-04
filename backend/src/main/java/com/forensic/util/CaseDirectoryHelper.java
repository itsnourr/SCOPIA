package com.forensic.util;

import java.io.File;

public class CaseDirectoryHelper {

    public static File getCaseDir(String baseDir, Long caseId) {
        File caseDir = new File(baseDir, String.valueOf(caseId));
        if (!caseDir.exists()) caseDir.mkdirs();

        // Ensure subdirectories
        File outputDir = new File(caseDir, "output");
        if (!outputDir.exists()) outputDir.mkdirs();

        File encryptedDir = new File(caseDir, "encrypted_images");
        if (!encryptedDir.exists()) encryptedDir.mkdirs();

        File tempDir = new File(caseDir, "temp");
        if (!tempDir.exists()) tempDir.mkdirs();

        return caseDir;
    }

    public static File getOutputDir(String baseDir, Long caseId) {
        return new File(getCaseDir(baseDir, caseId), "output");
    }

    public static File getEncryptedDir(String baseDir, Long caseId) {
        return new File(getCaseDir(baseDir, caseId), "encrypted_images");
    }

    public static File getTempDir(String baseDir, Long caseId) {
        return new File(getCaseDir(baseDir, caseId), "temp");
    }
}