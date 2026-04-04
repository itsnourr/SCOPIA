package com.forensic.controller;

import com.forensic.dto.*;
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
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/image")
public class ImageController {

    @Autowired private CryptoService cryptoService;
    @Autowired private HmacService hmacService;
    @Autowired private ImageRepository imageRepository;
    @Autowired private CaseRepository caseRepository;

    @Value("${app.upload.dir}") private String uploadDir;

    @PostMapping("/upload")
    public ResponseEntity<?> uploadImage(
            @RequestParam("file") MultipartFile file,
            @RequestParam("caseId") Long caseId,
            @RequestParam(value = "description", required = false) String description) {

        try {
            if (file.isEmpty()) return ResponseEntity.badRequest().body("File is empty");

            Optional<Case> caseOptional = caseRepository.findById(caseId);
            if (caseOptional.isEmpty()) return ResponseEntity.badRequest().body("Case not found");

            // Ensure directories
            File encryptedDir = CaseDirectoryHelper.getEncryptedDir(uploadDir, caseId);
            File tempDir = CaseDirectoryHelper.getTempDir(uploadDir, caseId);

            // Unique filename
            String originalFilename = file.getOriginalFilename();
            String uniqueFilename = UUID.randomUUID() + "_" + originalFilename;

            Path tempFile = Paths.get(tempDir.getAbsolutePath(), "temp_" + uniqueFilename);
            file.transferTo(tempFile.toFile());

            String encryptedPath = Paths.get(encryptedDir.getAbsolutePath(), uniqueFilename).toString();
            String[] ivHolder = new String[1];
            cryptoService.encrypt(tempFile.toString(), encryptedPath, ivHolder);
            Files.delete(tempFile);

            byte[] encryptedData = cryptoService.readEncryptedFile(encryptedPath);
            String hmac = hmacService.generateHmac(encryptedData);

            Image image = new Image();
            image.setCaseEntity(caseOptional.get());
            image.setFilename(originalFilename);
            image.setFilepath(encryptedPath);
            image.setIvBase64(ivHolder[0]);
            image.setHmacBase64(hmac);

            Image savedImage = imageRepository.save(image);

            return ResponseEntity.status(HttpStatus.CREATED).body(
                    new ImageUploadResponse(
                            savedImage.getImageId(),
                            savedImage.getFilename(),
                            "Image uploaded and encrypted successfully",
                            ivHolder[0],
                            hmac));

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error uploading image: " + e.getMessage());
        }
    }

    @PostMapping("/add")
    public ResponseEntity<?> addImage(@RequestBody ImageAddRequest request) {
        try {
            Optional<Case> caseOptional = caseRepository.findById(request.getCaseId());
            if (caseOptional.isEmpty()) return ResponseEntity.badRequest().body("Case not found");

            Image image = new Image();
            image.setCaseEntity(caseOptional.get());
            image.setFilename(request.getFilename());
            image.setFilepath(request.getFilepath());
            image.setIvBase64(request.getIvBase64());
            image.setHmacBase64(request.getHmacBase64());

            return ResponseEntity.status(HttpStatus.CREATED).body(imageRepository.save(image));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error adding image: " + e.getMessage());
        }
    }

    @GetMapping("/view/{id}")
    public ResponseEntity<?> viewImage(@PathVariable Long id) {
        try {
            Optional<Image> opt = imageRepository.findById(id);
            if (opt.isEmpty()) return ResponseEntity.notFound().build();

            Image image = opt.get();
            File encryptedFile = new File(image.getFilepath());
            if (!encryptedFile.exists())
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Encrypted image file not found");

            byte[] encryptedData = cryptoService.readEncryptedFile(image.getFilepath());
            if (!hmacService.verifyHmac(encryptedData, image.getHmacBase64()))
                return ResponseEntity.status(HttpStatus.FORBIDDEN)
                        .body("Image integrity check failed");

            byte[] decryptedData = cryptoService.decrypt(image.getFilepath());
            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(getContentType(image.getFilename())))
                    .header("Content-Disposition", "inline; filename=\"" + image.getFilename() + "\"")
                    .body(decryptedData);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error viewing image: " + e.getMessage());
        }
    }

    @GetMapping("/verify/{id}")
    public ResponseEntity<?> verifyImage(@PathVariable Long id) {
        try {
            Optional<Image> opt = imageRepository.findById(id);
            if (opt.isEmpty()) return ResponseEntity.notFound().build();

            Image image = opt.get();
            byte[] encryptedData = cryptoService.readEncryptedFile(image.getFilepath());
            boolean valid = hmacService.verifyHmac(encryptedData, image.getHmacBase64());

            return ResponseEntity.ok(new ImageVerifyResponse(
                    image.getImageId(),
                    image.getFilename(),
                    valid,
                    valid ? "Integrity verified" : "Integrity FAILED"
            ));
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ImageVerifyResponse(null, null, false,
                            "Error verifying image: " + e.getMessage()));
        }
    }

    @GetMapping("/list/{caseId}")
    public ResponseEntity<?> listImagesByCase(@PathVariable Long caseId) {
        try {
            List<Image> images = imageRepository.findByCaseEntity_CaseId(caseId);
            List<ImageListItemResponse> list = images.stream().map(img -> {
                ImageListItemResponse resp = new ImageListItemResponse();
                resp.setImageId(img.getImageId());
                resp.setFilename(img.getFilename());
                resp.setFilepath(img.getFilepath());
                resp.setIvBase64(img.getIvBase64());
                resp.setHmacBase64(img.getHmacBase64());
                resp.setUploadedAt(img.getUploadedAt());
                resp.setViewUrl("/api/image/view/" + img.getImageId());
                resp.setVerifyUrl("/api/image/verify/" + img.getImageId());
                return resp;
            }).collect(Collectors.toList());
            return ResponseEntity.ok(list);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error listing images: " + e.getMessage());
        }
    }

    @DeleteMapping("/{imageId}")
    public ResponseEntity<?> deleteImage(@PathVariable Long imageId) {
        try {
            Optional<Image> opt = imageRepository.findById(imageId);
            if (opt.isEmpty()) return ResponseEntity.status(HttpStatus.NOT_FOUND).body("Image not found");

            Image image = opt.get();
            imageRepository.delete(image);
            Files.deleteIfExists(Paths.get(image.getFilepath()));

            return ResponseEntity.ok("Image deleted successfully");
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error deleting image: " + e.getMessage());
        }
    }

    private String getContentType(String filename) {
        String ext = filename.substring(filename.lastIndexOf('.') + 1).toLowerCase();
        return switch (ext) {
            case "jpg", "jpeg" -> "image/jpeg";
            case "png" -> "image/png";
            case "gif" -> "image/gif";
            case "bmp" -> "image/bmp";
            case "webp" -> "image/webp";
            default -> "application/octet-stream";
        };
    }
}