package com.forensic.controller;

import com.forensic.entity.Case;
import com.forensic.entity.Image;
import com.forensic.repository.CaseRepository;
import com.forensic.repository.ImageRepository;
import com.forensic.service.CryptoService;
import com.forensic.service.HmacService;
import com.forensic.util.CaseDirectoryHelper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

@RestController
@RequestMapping("/api/telemetry")
public class TelemetryController {

    @Autowired private CaseRepository caseRepository;
    @Autowired private ImageRepository imageRepository;
    @Autowired private CryptoService cryptoService;
    @Autowired private HmacService hmacService;

    @Value("${app.upload.dir}") private String uploadDir;

    @PostMapping("/{caseId}/images")
    public ResponseEntity<?> uploadTelemetryImages(
            @PathVariable Long caseId,
            @RequestParam("images") MultipartFile[] images) {

        try {
            Optional<Case> caseOpt = caseRepository.findById(caseId);
            if (caseOpt.isEmpty()) return ResponseEntity.badRequest().body("Case not found");

            File encryptedDir = CaseDirectoryHelper.getEncryptedDir(uploadDir, caseId);
            File tempDir = CaseDirectoryHelper.getTempDir(uploadDir, caseId);

            int counter = encryptedDir.listFiles((d, name) -> name.startsWith("image_")) != null
                    ? encryptedDir.listFiles((d, name) -> name.startsWith("image_")).length + 1
                    : 1;

            List<Image> saved = new ArrayList<>();
            for (MultipartFile file : images) {
                if (file.isEmpty()) continue;

                String ext = getExtension(file.getOriginalFilename());
                String filename = String.format("image_%03d.%s", counter++, ext);

                Path tempPath = Paths.get(tempDir.getAbsolutePath(), "temp_" + filename);
                file.transferTo(tempPath.toFile());

                String encryptedPath = Paths.get(encryptedDir.getAbsolutePath(), filename).toString();
                String[] ivHolder = new String[1];
                cryptoService.encrypt(tempPath.toString(), encryptedPath, ivHolder);
                Files.delete(tempPath);

                byte[] encryptedData = cryptoService.readEncryptedFile(encryptedPath);
                String hmac = hmacService.generateHmac(encryptedData);

                Image image = new Image();
                image.setCaseEntity(caseOpt.get());
                image.setFilename(filename);
                image.setFilepath(encryptedPath);
                image.setIvBase64(ivHolder[0]);
                image.setHmacBase64(hmac);

                saved.add(imageRepository.save(image));
            }

            return ResponseEntity.status(HttpStatus.CREATED)
                    .body("Uploaded " + saved.size() + " images");

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error uploading telemetry images: " + e.getMessage());
        }
    }

    private String getExtension(String filename) {
        if (filename == null || !filename.contains(".")) return "jpg";
        return filename.substring(filename.lastIndexOf('.') + 1);
    }
}