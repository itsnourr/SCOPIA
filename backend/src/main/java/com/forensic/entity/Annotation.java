package com.forensic.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "annotations")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Annotation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "annotation_id")
    private Long annotationId;

    @Column(name = "annotation_desc", nullable = false, length = 10)
    private String annotationDesc; 

    @Column(name = "x_coord", nullable = false)
    private Float xCoord;

    @Column(name = "y_coord", nullable = false)
    private Float yCoord;

    @Column(name = "z_coord", nullable = false)
    private Float zCoord;
}