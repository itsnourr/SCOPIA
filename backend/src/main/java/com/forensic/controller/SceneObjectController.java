package com.forensic.controller;

import com.forensic.util.CaseDirectoryHelper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.io.FileInputStream;

@RestController
@RequestMapping("/api/scene")
public class SceneObjectController {

    @Value("${app.upload.dir}") private String uploadDir;

    @GetMapping("/{caseId}/model")
    public ResponseEntity<?> getSceneModel(@PathVariable Long caseId) {
        try {
            File modelFile = new File(CaseDirectoryHelper.getOutputDir(uploadDir, (long) caseId), "meshed-poisson.ply");
            if (!modelFile.exists()) return ResponseEntity.notFound().build();

            InputStreamResource resource = new InputStreamResource(new FileInputStream(modelFile));
            return ResponseEntity.ok()
                    .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=meshed-poisson.ply")
                    .contentType(MediaType.APPLICATION_OCTET_STREAM)
                    .contentLength(modelFile.length())
                    .body(resource);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError()
                    .body("Error loading 3D model: " + e.getMessage());
        }
    }
}