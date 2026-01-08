package com.forensic.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * DTO for image list items with view URL
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class ImageListItemResponse {
    private Long imageId;
    private String filename;
    private String filepath;
    private String ivBase64;
    private String hmacBase64;
    private LocalDateTime uploadedAt;
    private String viewUrl; // URL to view the decrypted image
    private String verifyUrl; // URL to verify image integrity
    private String base64Data; // Base64-encoded image data (only included if includeData=true)
    private String dataUrl; // Data URL format (data:image/jpeg;base64,...) for direct use in img tags
}

