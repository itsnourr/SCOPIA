import React from 'react';
import { useNavigate } from "react-router-dom";
import { useState, useEffect, useRef } from "react";

import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Toast } from "primereact/toast";

function LoginScreen() {

    const navigateTo = useNavigate();
    const toast = useRef(null);

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [signingUp, setSigningUp] = useState(false);
    const [signupError, setSignupError] = useState(null);
    const [signupSuccess, setSignupSuccess] = useState(false);

    function authenticate() {
        if (!username || !password) {
            toast.current?.show({
                severity: 'error',
                summary: 'Validation Error',
                detail: 'Please enter both username and password',
                life: 3000
            });
            return;
        }

        fetch("/api/user/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        })
            .then(response => {
                if (!response.ok) {
                    // Show error toast for failed login
                    toast.current?.show({
                        severity: 'error',
                        summary: 'Login Failed',
                        detail: 'Login failed. Please check your credentials and try again.',
                        life: 3000
                    });
                    return null;
                }
                return response.json();
            })
            .then(data => {
                if (data) {
                    // Only navigate if login was successful
                    console.log("Login successful:", data);
                    navigateTo("/cases");
                }
            })
            .catch(error => {
                console.error("Error logging user in", error);
                toast.current?.show({
                    severity: 'error',
                    summary: 'Login Failed',
                    detail: 'Login failed. Please try again.',
                    life: 3000
                });
            });
    }

    function handleSignup() {
        if (!username || !password) {
            setSignupError("Username and password are required");
            return;
        }

        setSigningUp(true);
        setSignupError(null);
        setSignupSuccess(false);

        fetch("/api/user/signup", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.message || `Signup failed! status: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log("Signup successful:", data);
                setSignupSuccess(true);
                setSignupError(null);
                
                // Clear success message after 3 seconds
                setTimeout(() => {
                    setSignupSuccess(false);
                }, 3000);
            })
            .catch(error => {
                console.error("Error signing up:", error);
                setSignupError(error.message || "Failed to create account");
            })
            .finally(() => {
                setSigningUp(false);
            });
    }

    return (
        <div style={{ marginBottom: "260px" }} >
            <Toast ref={toast} />

            <h1 style={{ fontSize: "140px", marginTop: "48px", marginBottom: "0", marginLeft: "50px" }}>🔐</h1>
            <h1>Login using your credentials</h1>

            <div style={{ textAlign: "right", marginRight: "100px" }} >

                <div style={{ marginBottom: "20px" }}>
                    <label style={{ marginRight: "10px", fontSize: "24px" }}> Enter your name: </label>
                    <InputText onChange={(e) => setUsername(e.target.value)} />
                </div>

                <div>
                    <label style={{ marginRight: "10px", fontSize: "24px" }}> Enter your password: </label>
                    <Password id="pwd" value={password} onChange={(e) => setPassword(e.target.value)} feedback={false} />
                </div>

            </div>

            <div style={{ marginTop: "40px", display: "flex", gap: "10px", justifyContent: "center" }}>
                <button type="button" onClick={authenticate}> Login </button>
                <button type="button" onClick={handleSignup} disabled={signingUp}>
                    {signingUp ? 'Signing up...' : 'Signup'}
                </button>
            </div>
            
            {signupSuccess && (
                <p style={{ color: "green", marginTop: "10px", textAlign: "center" }}>
                    Account created successfully! You can now login.
                </p>
            )}
            {signupError && (
                <p style={{ color: "red", marginTop: "10px", textAlign: "center" }}>
                    Signup error: {signupError}
                </p>
            )}

        </div>
    );
}

export default LoginScreen;