package com.forensic.controller;

import com.forensic.entity.Image;
import com.forensic.repository.ImageRepository;
import com.forensic.service.CryptoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

@RestController
@RequestMapping("/api/colmap")
public class ColmapController {

    @Autowired
    private CryptoService cryptoService;

    @Autowired
    private ImageRepository imageRepository;

    @Value("${app.upload.dir}")
    private String uploadDir;

    @GetMapping("/run")
    public ResponseEntity<String> runColmapPipeline(@RequestParam("caseId") Long caseId) {
        if (caseId == null) {
            return ResponseEntity.badRequest().body("caseId parameter is required");
        }

        try {
            // Case folder
            String caseIdAsString = String.valueOf(caseId);
            File caseFolder = new File(uploadDir, caseIdAsString);
            File rawFolder = new File(caseFolder, "raw_images");

            // Ensure raw_images folder exists
            if (!rawFolder.exists()) rawFolder.mkdirs();

            List<Image> images = imageRepository.findByCaseEntity_CaseId(caseId);
            for (Image img : images) {
                byte[] decrypted = cryptoService.decrypt(img.getFilepath());
                Path target = Paths.get(rawFolder.getAbsolutePath(), img.getFilename());
                Files.write(target, decrypted);
            }

            // Locate PowerShell script
            String baseDir = System.getProperty("user.dir");
            File scriptFile = new File(baseDir, "scripts/colmap.ps1");
            if (!scriptFile.exists()) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body("Colmap script not found at: " + scriptFile.getAbsolutePath());
            }

            // Run PS1 script
            ProcessBuilder pb = new ProcessBuilder(
                    "powershell.exe",
                    "-ExecutionPolicy", "Bypass",
                    "-File",
                    scriptFile.getAbsolutePath(),
                    "-caseId",
                    caseIdAsString,
                     "-uploadDir",
                    uploadDir
            );
            pb.redirectErrorStream(true);
            Process process = pb.start();

            // Capture output
            StringBuilder output = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append("\n");
                }
            }

            int exitCode = process.waitFor();

            // Cleanup raw_images folder
            Files.walk(rawFolder.toPath())
                    .map(Path::toFile)
                    .sorted((a, b) -> -a.compareTo(b)) // delete files before dirs
                    .forEach(File::delete);

            if (exitCode != 0) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body("Colmap script failed:\n" + output);
            }

            return ResponseEntity.ok("Colmap executed successfully:\n" + output);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error running Colmap pipeline: " + e.getMessage());
        }
    }
}