package com.forensic.repository;

import com.forensic.entity.Link;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface LinkRepository extends JpaRepository<Link, Long> {
    List<Link> findByCaseKey(String caseKey);
    void deleteByCaseKeyAndNodeIdFromOrNodeIdTo(
        String caseKey, Long from, Long to
    );
}

