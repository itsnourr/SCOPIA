package com.forensic.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "nodes")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Node {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "node_id")
    private Long nodeId;

    @Column(name = "case_key", nullable = false, length = 50)
    private String caseKey;

    @Column(name = "node_type", nullable = false, length = 10)
    private String nodeType; // "SUSPECT", "CLUE"

    @Column(name = "node_reference", nullable = false)
    private Long nodeReference;

    // React Flow position persistence
    @Column(name = "pos_x", nullable = false)
    private Double posX;

    @Column(name = "pos_y", nullable = false)
    private Double posY;
}
