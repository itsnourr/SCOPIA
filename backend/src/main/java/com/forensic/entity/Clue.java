package com.forensic.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "clues")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Clue {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "clue_id")
    private Long clueId;

    @Column(length = 100)
    private String type;

    @Column(length = 100)
    private String category;

    @Column(name = "picker_id")
    private Long pickerId; // References User.userId

    @Column(name = "clue_desc", length = 500)
    private String clueDesc;

    @Column(length = 100)
    private String coordinates;
}