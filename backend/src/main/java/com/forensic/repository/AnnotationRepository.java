package com.forensic.repository;

import com.forensic.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface AnnotationRepository extends JpaRepository<User, Long> {
    
}

