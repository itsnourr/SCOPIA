package com.forensic.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class TeamDto {
    private Long caseId;
    private List<Long> userIds;
}
