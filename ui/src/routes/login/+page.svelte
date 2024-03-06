<!-- Login.svelte -->
<script>
    import loginCreds from '../../.secrets/otherSecrets.json'
    let username = '';
    let password = '';


    function handleLogin() {
        if (username === 'admin' && password === loginCreds.loginPass) {
            localStorage.setItem('authenticated', 'true');
            // Redirect the user to the main page or any authenticated route
            window.location.href = '/';
        } else {
            alert('Invalid username or password');
        }
    }
</script>

<label>
    Username:
    <input type="text" bind:value={username} />
</label>
<label>
    Password:
    <input type="password" bind:value={password} />
</label>
<button on:click={handleLogin}>Login</button>