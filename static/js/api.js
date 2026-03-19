const API = {
    baseURL: 'http://localhost:5000/api',
    
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            // Não autorizado - redirecionar para login
            window.location.href = '/login';
            return null;
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.erro || 'Erro na requisição');
        }
        
        return data;
    },
    
    // Equipamentos
    getEquipamentos(filtros = {}) {
        const params = new URLSearchParams(filtros).toString();
        return this.request(`/equipamentos${params ? '?' + params : ''}`);
    },
    
    getEquipamento(id) {
        return this.request(`/equipamentos/${id}`);
    },
    
    criarEquipamento(dados) {
        return this.request('/equipamentos', {
            method: 'POST',
            body: JSON.stringify(dados)
        });
    },
    
    atualizarEquipamento(id, dados) {
        return this.request(`/equipamentos/${id}`, {
            method: 'PUT',
            body: JSON.stringify(dados)
        });
    },
    
    deletarEquipamento(id) {
        return this.request(`/equipamentos/${id}`, {
            method: 'DELETE'
        });
    },
    
    moverEquipamento(id, status) {
        return this.request(`/equipamentos/${id}/mover`, {
            method: 'PATCH',
            body: JSON.stringify({ status })
        });
    },
    
    getEstatisticas() {
        return this.request('/equipamentos/estatisticas');
    },
    
    // Usuários (se precisar)
    getUsuarios() {
        return this.request('/usuarios');
    },
    
    getUsuario(id) {
        return this.request(`/usuarios/${id}`);
    }
};