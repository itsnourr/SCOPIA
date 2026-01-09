package com.forensic.repository;

import com.forensic.entity.Clue;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface ClueRepository extends JpaRepository<Clue, Integer> {
    Page<Clue> findAll(Pageable pageable);
}