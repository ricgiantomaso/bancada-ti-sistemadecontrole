// Verificar autenticação
async function verificarAuth() {
    try {
        const response = await fetch('/api/verificar-sessao');
        const data = await response.json();
        
        if (!data.logado) {
            window.location.href = '/login';
            return false;
        }
        
        // Atualizar nome do usuário na navbar
        const userDisplay = document.getElementById('userNameDisplay');
        if (userDisplay) {
            const usuarioSalvo = localStorage.getItem('usuario');
            if (usuarioSalvo) {
                const usuario = JSON.parse(usuarioSalvo);
                userDisplay.textContent = usuario.nome_completo || usuario.usuario;
            } else {
                userDisplay.textContent = data.usuario?.nome || 'Técnico';
            }
        }
        
        return true;
    } catch (error) {
        console.error('Erro ao verificar autenticação:', error);
        window.location.href = '/login';
        return false;
    }
}

// Logout
async function logout() {
    if (confirm('Deseja realmente sair do sistema?')) {
        localStorage.removeItem('token');
        localStorage.removeItem('usuario');
        window.location.href = '/logout';
    }
}

// Executar verificação em todas as páginas protegidas
document.addEventListener('DOMContentLoaded', verificarAuth);