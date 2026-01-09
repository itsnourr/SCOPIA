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

    @Transactional
    public Clue addClue(Clue clue) {
        // Ensure pickerId corresponds to valid user (optional validation)
        return clueRepository.save(clue);
    }
}