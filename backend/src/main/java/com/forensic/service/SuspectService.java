package com.forensic.service;


import com.forensic.entity.Suspect;
import com.forensic.repository.SuspectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class SuspectService {
    
    private final SuspectRepository suspectRepository;

    public Page<Suspect> getSuspectsByCaseIdWithPagination(Long caseId, Pageable pageable) {
        return suspectRepository.findByCaseId(caseId, pageable);
    }

    @Transactional
    public Suspect addSuspect(Suspect suspect) {
        // Ensure any necessary validation (e.g., caseId exists) is done before saving
        return suspectRepository.save(suspect);
    }

}
