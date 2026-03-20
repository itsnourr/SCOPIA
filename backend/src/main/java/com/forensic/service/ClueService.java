package com.forensic.service;

import com.forensic.entity.Clue;
import com.forensic.repository.ClueRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ClueService {

    private final ClueRepository clueRepository;

    public Page<Clue> getCluesWithPagination(Pageable pageable) {
        return clueRepository.findAll(pageable);
    }

    public Page<Clue> getCluesByCaseIdWithPagination(Long caseId, Pageable pageable) {
        return clueRepository.findByCaseId(caseId, pageable);
    }

    @Transactional
    public Clue addClue(Clue clue) {
        // Ensure pickerId corresponds to valid user (optional validation)
        return clueRepository.save(clue);
    }

    // add clues by bulk with pickerid = 0 for rover given caseid
    @Transactional
    public void addRoverCluesByBulk(Long caseId, Iterable<Clue> clues) {
        for (Clue clue : clues) {
            clue.setCaseId(caseId);
            clue.setPickerId(0L); // 0 indicates rover
        }
        clueRepository.saveAll(clues);
    }

}