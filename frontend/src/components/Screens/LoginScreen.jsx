import React from 'react';
import { useNavigate } from "react-router-dom";
import { useState, useEffect, useRef } from "react";

import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Toast } from "primereact/toast";

import { login, signup } from "../../services/UserService";

function LoginScreen() {

    const navigateTo = useNavigate();
    const toast = useRef(null);

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [signingUp, setSigningUp] = useState(false);
    const [signupError, setSignupError] = useState(null);
    const [signupSuccess, setSignupSuccess] = useState(false);

    async function authenticate() {
        if (!username || !password) {
            toast.current?.show({
            severity: 'error',
            summary: 'Validation Error',
            detail: 'Please enter both username and password',
            life: 3000
            });
            return;
        }

        try {
            const res = await login(username, password);
            console.log("Login successful:", res.data);
            localStorage.setItem("currentUsername", username);
            navigateTo("/cases"); 
        } catch (error) {
            toast.current?.show({
            severity: 'error',
            summary: 'Login Failed',
            detail: 'Login failed. Please check your credentials.',
            life: 3000
            });
        }
    }

    async function handleSignup() {
        if (!username || !password) {
            setSignupError("Username and password are required");
            return;
        }

        setSigningUp(true);
        setSignupError(null);
        setSignupSuccess(false);

        try {
            const res = await signup(username, password);
            console.log("Signup successful:", res.data);

            setSignupSuccess(true);
            setTimeout(() => setSignupSuccess(false), 3000);
        } catch (error) {
            setSignupError(
            error.response?.data?.message || "Failed to create account"
            );
        } finally {
            setSigningUp(false);
        }
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