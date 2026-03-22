package com.forensic.dto;

import lombok.Data;

@Data
public class ImageAddRequest {
    private Long caseId;
    private String filename;
    private String filepath;
    private String ivBase64;
    private String hmacBase64;
}

