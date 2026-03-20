package com.forensic.service;

import com.forensic.entity.Case;
import com.forensic.repository.CaseAssignmentRepository;
import com.forensic.repository.CaseRepository;
import com.forensic.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Collections;
@Service
@RequiredArgsConstructor
public class CaseService {

    private final CaseRepository caseRepository;
    private final CaseAssignmentRepository caseAssignmentRepository;
    private final UserRepository userRepository;    

    public List<Case> listOpenCases() {
        return caseRepository.findByStatus("open"); 
    }

    public List<Case> listArchivedCases() {
        return caseRepository.findByStatus("archived");
    }

    public List<Case> listOpenCasesByUsername(String username) {
        Long userId = userRepository.findIdByUsername(username)
            .orElseThrow(() -> new RuntimeException("User not found"))
            .getUserId();
        System.out.println("Username " + username + " has id " + userId + "...");
        List<Long> caseIds = caseAssignmentRepository.findCaseIdsByUserId(userId);
        System.out.println("Cases with ids: " + caseIds);
        if (caseIds.isEmpty()) {
            return Collections.emptyList();
        }

        // 3️⃣ Get Cases with status 'open'
        return caseRepository.findByCaseIdInAndStatus(caseIds, "open");
        // return caseAssignmentRepository.findByStatusAndAssignedTo("open", userId);
    }

    
    public List<Case> listArchivedCasesByUsername(String username) {
        Long userId = userRepository.findIdByUsername(username)
            .orElseThrow(() -> new RuntimeException("User not found"))
            .getUserId();
        System.out.println("Username " + username + " has id " + userId + "...");
        List<Long> caseIds = caseAssignmentRepository.findCaseIdsByUserId(userId);
        System.out.println("Cases with ids: " + caseIds);
        if (caseIds.isEmpty()) {
            return Collections.emptyList();
        }

        // 3️⃣ Get Cases with status 'open'
        return caseRepository.findByCaseIdInAndStatus(caseIds, "archived");
        // return caseAssignmentRepository.findByStatusAndAssignedTo("open", userId);
    }

    // public List<Case> listArchivedCasesByUsername(String username) {
    //     Long userId = userRepository.findIdByUsername(username)
    //         .orElseThrow(() -> new RuntimeException("User not found"))
    //         .getUserId();
    //     return caseAssignmentRepository.findByStatusAndAssignedTo("archived", userId);
    // }

    public Page<Case> listActiveCasesWithPagination(Pageable pageable) {
        return caseRepository.findByStatus("open", pageable);
    }

    @Transactional
    public Case createCase(Case Case) {
        Case.setStatus("open");
        Case.setReportDate(LocalDateTime.now());
        return caseRepository.save(Case);
    }

    @Transactional
    public void archiveCase(Long caseId) {
        Case Case = caseRepository.findById(caseId)
            .orElseThrow(() -> new RuntimeException("Case not found"));
        Case.setStatus("archived");
        caseRepository.save(Case);
    }

    public Case getCaseDetails(Long caseId) {
        return caseRepository.findById(caseId)
            .orElseThrow(() -> new RuntimeException("Case not found"));
    }

    // Stub for PDF export – integrate with iText or similar later
    public byte[] exportCaseToPdf(Integer caseId) {
        return new byte[0];
    }
}