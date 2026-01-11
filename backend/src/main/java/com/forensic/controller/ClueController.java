package com.forensic.controller;

import com.forensic.entity.Clue;
import com.forensic.repository.ClueRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Optional;

@CrossOrigin(origins = "http://localhost:5173")
@RestController
@RequestMapping("/api/clue")
public class ClueController {

    @Autowired
    private ClueRepository clueRepository;

    /**
     * GET /api/clue/all
     * Returns all clues
     */
    @GetMapping("/all")
    public ResponseEntity<?> getAllClues() {
        try {
            List<Clue> clues = clueRepository.findAll();
            return ResponseEntity.ok(clues);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving clues: " + e.getMessage());
        }
    }

    /**
     * GET /api/clue/{id}
     * Returns a clue by ID
     */
    @GetMapping("/{id}")
    public ResponseEntity<?> getClueById(@PathVariable Long id) {
        try {
            Optional<Clue> clue = clueRepository.findById(id);

            if (clue.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Clue not found with id: " + id);
            }

            return ResponseEntity.ok(clue.get());

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving clue: " + e.getMessage());
        }
    }

    /**
     * POST /api/clue/create
     * Creates a new clue
     */
    @PostMapping("/create")
    public ResponseEntity<?> createClue(@RequestBody Clue clue) {
        try {
            Clue savedClue = clueRepository.save(clue);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedClue);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error creating clue: " + e.getMessage());
        }
    }

    /**
     * PUT /api/clue/update/{id}
     * Updates an existing clue
     */
    @PutMapping("/update/{id}")
    public ResponseEntity<?> updateClue(
            @PathVariable Long id,
            @RequestBody Clue updatedClue) {

        try {
            Optional<Clue> existingClueOpt = clueRepository.findById(id);

            if (existingClueOpt.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Clue not found with id: " + id);
            }

            Clue existingClue = existingClueOpt.get();

            // Update allowed fields
            existingClue.setType(updatedClue.getType());
            existingClue.setPickerId(updatedClue.getPickerId());
            existingClue.setClueDesc(updatedClue.getClueDesc());
            existingClue.setCoordinates(updatedClue.getCoordinates());
            existingClue.setAnnotationLink(updatedClue.getAnnotationLink());

            Clue savedClue = clueRepository.save(existingClue);
            return ResponseEntity.ok(savedClue);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error updating clue: " + e.getMessage());
        }
    }

    /**
     * DELETE /api/clue/delete/{id}
     * Deletes a clue
     */
    @DeleteMapping("/delete/{id}")
    public ResponseEntity<?> deleteClue(@PathVariable Long id) {
        try {
            if (!clueRepository.existsById(id)) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Clue not found with id: " + id);
            }

            clueRepository.deleteById(id);
            return ResponseEntity.ok("Clue deleted successfully");

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error deleting clue: " + e.getMessage());
        }
    }
}
