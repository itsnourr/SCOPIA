package com.forensic.repository;

import com.forensic.entity.Node;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface NodeRepository extends JpaRepository<Node, Long> {
    // List<Node> findByCaseKey(String caseKey);
    // boolean existsByCaseKeyAndNodeTypeAndNodeReference(
    //     String caseKey, String nodeType, Long nodeReference
    // );
    // void deleteByCaseKey(String caseKey);
    List<Node> findByCaseId(Long caseId);
    void deleteByCaseId(Long caseId);
}
