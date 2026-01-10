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

    @Column(name = "node_type", nullable = false, length = 10)
    private String nodeType; // e.g., "SUSPECT"

    @Column(name = "node_reference", nullable = false)
    private Long nodeReference; // e.g., suspect_id
}