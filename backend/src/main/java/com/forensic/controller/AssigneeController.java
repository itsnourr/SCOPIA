package com.forensic.controller;

import com.forensic.entity.User;
import com.forensic.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@CrossOrigin(origins = "http://localhost:5173")
@RestController
@RequestMapping("/api/assignee")
public class AssigneeController {

    @Autowired
    private UserService userService;

    /**
     * GET /api/assignee/case/{caseId}/users
     * Coworker: users assigned to a specific case
     */
    @GetMapping("/case/{caseId}/users")
    public ResponseEntity<?> getUsersForCase(@PathVariable Long caseId) {
        try {
            List<User> users = userService.getUsersForCase(caseId);
            return ResponseEntity.ok(users);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving users for case " + caseId + ": " + e.getMessage());
        }
    }

    /**
     * GET /api/assignee/criminologists
     * Leader: all users with role "criminologist"
     */
    @GetMapping("/criminologists")
    public ResponseEntity<?> getCriminologists() {
        try {
            List<User> users = userService.getCriminologists();
            return ResponseEntity.ok(users);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving criminologists: " + e.getMessage());
        }
    }

    /**
     * GET /api/assignee/all
     * Superadmin: all users
     */
    @GetMapping("/all")
    public ResponseEntity<?> getAllUsers() {
        try {
            List<User> users = userService.getAllUsers();
            return ResponseEntity.ok(users);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving users: " + e.getMessage());
        }
    }
}
