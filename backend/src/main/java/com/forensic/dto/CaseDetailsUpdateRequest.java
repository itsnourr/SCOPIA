package com.forensic.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class CaseDetailsUpdateRequest {
    private String location;
    private String coordinates;
    private LocalDateTime reportDate;
    private LocalDateTime crimeTime;
}