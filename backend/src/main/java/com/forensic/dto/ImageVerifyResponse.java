package com.forensic.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ImageVerifyResponse {
    private Long imageId;
    private String filename;
    private boolean isValid;
    private String message;
}

