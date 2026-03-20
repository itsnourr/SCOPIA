package com.forensic.repository;

import com.forensic.entity.Suspect;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface SuspectRepository extends JpaRepository<Suspect, Long> {
    Page<Suspect> findByCaseId(Long caseId, Pageable pageable);
}
