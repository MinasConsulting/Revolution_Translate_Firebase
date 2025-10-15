<script>
    import loginCreds from '../../.secrets/otherSecrets.json'
    let username = '';
    let password = '';
    let isLoading = false;
    let error = '';

    async function handleLogin() {
        error = '';
        isLoading = true;

        setTimeout(() => {
            if (username === 'admin' && password === loginCreds.loginPass) {
                localStorage.setItem('authenticated', 'true');
                window.location.href = '/';
            } else {
                error = 'Invalid username or password';
                isLoading = false;
            }
        }, 300);
    }

    function handleKeyPress(event) {
        if (event.key === 'Enter') {
            handleLogin();
        }
    }
</script>

<svelte:head>
    <title>Login - Revolution Translate</title>
</svelte:head>

<div class="login-container">
    <div class="login-card">
        <div class="login-header">
            <img src="/Revolution Church - Full Horiztonal Black SM.png" alt="Revolution Church" class="logo">
            <h1>Translation Portal</h1>
            <p class="subtitle">Sign in to continue</p>
        </div>

        {#if error}
            <div class="error-message">
                {error}
            </div>
        {/if}

        <form on:submit|preventDefault={handleLogin} class="login-form">
            <div class="form-group">
                <label for="username">Username</label>
                <input 
                    id="username"
                    type="text" 
                    bind:value={username} 
                    on:keypress={handleKeyPress}
                    placeholder="Enter your username"
                    disabled={isLoading}
                    autocomplete="username"
                    required
                />
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input 
                    id="password"
                    type="password" 
                    bind:value={password}
                    on:keypress={handleKeyPress}
                    placeholder="Enter your password"
                    disabled={isLoading}
                    autocomplete="current-password"
                    required
                />
            </div>

            <button type="submit" class="primary login-button" disabled={isLoading}>
                {#if isLoading}
                    Signing in...
                {:else}
                    Sign In
                {/if}
            </button>
        </form>

        <div class="login-footer">
            <p>Revolution Church Translation System</p>
        </div>
    </div>
</div>

<style>
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: var(--spacing-lg);
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
    }

    .login-card {
        width: 100%;
        max-width: 440px;
        background-color: var(--color-surface-elevated);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-xl);
        padding: var(--spacing-2xl);
        box-shadow: var(--shadow-xl);
        animation: slideUp 0.4s ease-out;
    }

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .login-header {
        text-align: center;
        margin-bottom: var(--spacing-xl);
    }

    .logo {
        width: 100%;
        max-width: 280px;
        height: auto;
        margin-bottom: var(--spacing-lg);
        filter: brightness(0) invert(1);
    }

    .login-header h1 {
        font-size: var(--font-size-3xl);
        margin-bottom: var(--spacing-sm);
        color: var(--color-text);
    }

    .subtitle {
        font-size: var(--font-size-base);
        color: var(--color-text-secondary);
        margin: 0;
    }

    .error-message {
        background-color: rgba(244, 67, 54, 0.1);
        border: 1px solid var(--color-error);
        color: var(--color-error);
        padding: var(--spacing-md);
        border-radius: var(--radius-md);
        margin-bottom: var(--spacing-lg);
        text-align: center;
        font-size: var(--font-size-sm);
        animation: shake 0.3s ease-in-out;
    }

    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }

    .login-form {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-lg);
    }

    .form-group {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
    }

    .form-group label {
        font-size: var(--font-size-sm);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text);
    }

    .form-group input {
        padding: var(--spacing-md);
        font-size: var(--font-size-base);
    }

    .login-button {
        margin-top: var(--spacing-md);
        padding: var(--spacing-md) var(--spacing-xl);
        font-size: var(--font-size-lg);
        font-weight: var(--font-weight-semibold);
        width: 100%;
    }

    .login-footer {
        margin-top: var(--spacing-xl);
        padding-top: var(--spacing-lg);
        border-top: 1px solid var(--color-border);
        text-align: center;
    }

    .login-footer p {
        font-size: var(--font-size-sm);
        color: var(--color-text-muted);
        margin: 0;
    }

    @media (max-width: 480px) {
        .login-card {
            padding: var(--spacing-xl);
        }

        .logo {
            max-width: 220px;
        }

        .login-header h1 {
            font-size: var(--font-size-2xl);
        }
    }
</style>
