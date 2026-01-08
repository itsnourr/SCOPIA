package com.forensic.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ImageUploadResponse {
    private Long imageId;
    private String filename;
    private String message;
    private String ivBase64;
    private String hmacBase64;
}

