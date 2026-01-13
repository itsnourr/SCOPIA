package com.forensic.service;

import com.forensic.entity.User;
import com.forensic.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    /**
     * Coworker:
     * Users assigned to a specific case
     * (IMPLEMENTATION PLACEHOLDER)
     */
    public List<User> getUsersForCase(Long caseId) {
        /*
         * TODO:
         * Replace this with actual case-user mapping logic
         * Example later:
         * return caseUserRepository.findUsersByCaseId(caseId);
         */
        throw new UnsupportedOperationException(
                "Case-user assignment logic not implemented yet"
        );
    }

    /**
     * Leader:
     * All users with role "criminologist"
     */
    public List<User> getCriminologists() {
        return userRepository.findByRole("criminologist");
    }

    /**
     * Extra:
     * All users with role "lead"
     */
    public List<User> getLeaders() {
        return userRepository.findByRole("lead");
    }

    /**
     * Superadmin:
     * All users
     */
    public List<User> getAllUsers() {
        return userRepository.findAll();
    }
}
