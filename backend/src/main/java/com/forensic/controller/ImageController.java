package com.forensic.controller;

import com.forensic.dto.ImageListItemResponse;
import com.forensic.dto.ImageUploadResponse;
import com.forensic.dto.ImageVerifyResponse;
import com.forensic.entity.Case;
import com.forensic.entity.Image;
import com.forensic.repository.CaseRepository;
import com.forensic.repository.ImageRepository;
import com.forensic.service.CryptoService;
import com.forensic.service.HmacService;
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
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/image")
public class ImageController {

    @Autowired
    private CryptoService cryptoService;

    @Autowired
    private HmacService hmacService;

    @Autowired
    private ImageRepository imageRepository;

    @Autowired
    private CaseRepository caseRepository;

    @Value("${app.upload.dir}")
    private String uploadDir;

    /**
     * POST /api/image/upload
     * Encrypts and stores an image with HMAC for integrity
     */
    @PostMapping("/upload")
    public ResponseEntity<?> uploadImage(
            @RequestParam("file") MultipartFile file,
            @RequestParam("caseId") Long caseId,
            @RequestParam(value = "description", required = false) String description) {

        try {
            // Validate file
            if (file.isEmpty()) {
                return ResponseEntity.badRequest().body("File is empty");
            }

            // Check if case exists
            Optional<Case> caseOptional = caseRepository.findById(caseId);
            if (caseOptional.isEmpty()) {
                return ResponseEntity.badRequest().body("Case not found");
            }

            // Create upload directory if not exists
            File uploadDirectory = new File(uploadDir);
            if (!uploadDirectory.exists()) {
                uploadDirectory.mkdirs();
            }

            // Generate unique filename
            String originalFilename = file.getOriginalFilename();
            String uniqueFilename = UUID.randomUUID().toString() + "_" + originalFilename;

            // Save original file temporarily
            Path tempFilePath = Paths.get(uploadDir, "temp_" + uniqueFilename);
            file.transferTo(tempFilePath.toFile());

            // Encrypt the file
            String encryptedFilePath = Paths.get(uploadDir, uniqueFilename).toString();
            String[] ivHolder = new String[1];
            cryptoService.encrypt(tempFilePath.toString(), encryptedFilePath, ivHolder);

            // Delete temporary file
            Files.delete(tempFilePath);

            // Read encrypted file for HMAC generation
            byte[] encryptedData = cryptoService.readEncryptedFile(encryptedFilePath);

            // Generate HMAC
            String hmacBase64 = hmacService.generateHmac(encryptedData);

            // Save metadata to database
            Image image = new Image();
            image.setCaseEntity(caseOptional.get());
            image.setFilename(originalFilename);
            image.setFilepath(encryptedFilePath);
            image.setIvBase64(ivHolder[0]);
            image.setHmacBase64(hmacBase64);

            Image savedImage = imageRepository.save(image);

            return ResponseEntity.status(HttpStatus.CREATED).body(
                    new ImageUploadResponse(
                            savedImage.getImageId(),
                            savedImage.getFilename(),
                            "Image uploaded and encrypted successfully",
                            ivHolder[0],
                            hmacBase64));

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error uploading image: " + e.getMessage());
        }
    }

    /**
     * GET /api/image/view/{id}
     * Verifies integrity and returns decrypted image
     */
    @GetMapping("/view/{id}")
    public ResponseEntity<?> viewImage(@PathVariable Long id) {
        try {
            // Fetch image metadata
            Optional<Image> imageOptional = imageRepository.findById(id);
            if (imageOptional.isEmpty()) {
                return ResponseEntity.notFound().build();
            }

            Image image = imageOptional.get();

            // Check if file exists
            File encryptedFile = new File(image.getFilepath());
            if (!encryptedFile.exists()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Encrypted image file not found at: " + image.getFilepath());
            }

            // Read encrypted file
            byte[] encryptedData = cryptoService.readEncryptedFile(image.getFilepath());

            // Verify HMAC
            boolean isValid = hmacService.verifyHmac(encryptedData, image.getHmacBase64());

            if (!isValid) {
                // Log for debugging
                System.err.println("⚠️ HMAC verification failed for image ID: " + id);
                System.err.println("   File path: " + image.getFilepath());
                System.err.println("   Stored HMAC: " + image.getHmacBase64());
                System.err.println("   File exists: " + encryptedFile.exists());
                System.err.println("   File size: " + encryptedFile.length() + " bytes");
                System.err.println("   ⚠️  POSSIBLE CAUSE: HMAC key in config/hmac.bin may have changed since upload!");
                System.err.println("   SOLUTION: Use the same HMAC key that was used when the image was uploaded.");

                return ResponseEntity.status(HttpStatus.FORBIDDEN)
                        .body("Image integrity check failed! The HMAC key may have changed since the image was uploaded. "
                                +
                                "Please ensure the HMAC key in config/hmac.bin matches the key used during upload. Image ID: "
                                + id);
            }

            // Decrypt image
            byte[] decryptedData = cryptoService.decrypt(image.getFilepath());

            // Determine content type based on filename
            String contentType = getContentType(image.getFilename());

            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(contentType))
                    .header("Content-Disposition", "inline; filename=\"" + image.getFilename() + "\"")
                    .header("Access-Control-Allow-Origin", "*")
                    .header("Access-Control-Allow-Methods", "GET, OPTIONS")
                    .header("Access-Control-Allow-Headers", "*")
                    .body(decryptedData);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error viewing image: " + e.getMessage());
        }
    }

    /**
     * GET /api/image/verify/{id}
     * Verifies image integrity without decryption
     */
    @GetMapping("/verify/{id}")
    public ResponseEntity<?> verifyImage(@PathVariable Long id) {
        try {
            // Fetch image metadata
            Optional<Image> imageOptional = imageRepository.findById(id);
            if (imageOptional.isEmpty()) {
                return ResponseEntity.notFound().build();
            }

            Image image = imageOptional.get();

            // Read encrypted file
            byte[] encryptedData = cryptoService.readEncryptedFile(image.getFilepath());

            // Verify HMAC
            boolean isValid = hmacService.verifyHmac(encryptedData, image.getHmacBase64());

            String message = isValid
                    ? "Image integrity verified successfully. No tampering detected."
                    : "ALERT: Image integrity check FAILED! File may have been tampered with.";

            return ResponseEntity.ok(new ImageVerifyResponse(
                    image.getImageId(),
                    image.getFilename(),
                    isValid,
                    message));

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ImageVerifyResponse(null, null, false,
                            "Error verifying image: " + e.getMessage()));
        }
    }

    /**
     * GET /api/image/list/{caseId}
     * Lists all images for a specific case with view URLs
     * Use the viewUrl to view images directly (same as /view/{id} endpoint)
     */
    @GetMapping("/list/{caseId}")
    public ResponseEntity<?> listImagesByCase(@PathVariable Long caseId) {
        try {
            List<Image> images = imageRepository.findByCaseEntity_CaseId(caseId);

            List<ImageListItemResponse> imageList = images.stream().map(image -> {
                ImageListItemResponse response = new ImageListItemResponse();
                response.setImageId(image.getImageId());
                response.setFilename(image.getFilename());
                response.setFilepath(image.getFilepath());
                response.setIvBase64(image.getIvBase64());
                response.setHmacBase64(image.getHmacBase64());
                response.setUploadedAt(image.getUploadedAt());
                response.setViewUrl("https://localhost:8443/api/image/view/" + image.getImageId());
                response.setVerifyUrl("https://localhost:8443/api/image/verify/" + image.getImageId());
                // base64Data and dataUrl are not included - use viewUrl to view images

                return response;
            }).collect(Collectors.toList());

            return ResponseEntity.ok(imageList);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error listing images: " + e.getMessage());
        }
    }

    private String getContentType(String filename) {
        String extension = filename.substring(filename.lastIndexOf(".") + 1).toLowerCase();
        switch (extension) {
            case "jpg":
            case "jpeg":
                return "image/jpeg";
            case "png":
                return "image/png";
            case "gif":
                return "image/gif";
            case "bmp":
                return "image/bmp";
            case "webp":
                return "image/webp";
            default:
                return "application/octet-stream";
        }
    }
}
