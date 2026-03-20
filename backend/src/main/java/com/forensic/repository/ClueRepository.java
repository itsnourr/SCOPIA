package com.forensic.repository;

import com.forensic.entity.Clue;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

// import java.util.List;

public interface ClueRepository extends JpaRepository<Clue, Long> {
    Page<Clue> findAll(Pageable pageable);
    Page<Clue> findByCaseId(Long caseId, Pageable pageable); 
}