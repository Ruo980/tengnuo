/**
 * PSM多资源池分析工具 - 前端增强脚本
 * 支持多资源池输入验证和交互
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('多资源池分析系统 - 增强版已加载');
    
    // 初始化表单验证
    initFormValidation();
    
    // 初始化实时验证
    initRealTimeValidation();
    
    // 初始化示例按钮
    initExampleButton();
});

/**
 * 初始化表单验证
 */
function initFormValidation() {
    const form = document.querySelector('form');
    if (!form) return;
    
    form.addEventListener('submit', function(event) {
        const targetPool = document.getElementById('target_pool').value.trim();
        const candidatePools = document.getElementById('candidate_pools').value.trim();
        
        let hasError = false;
        let errorMessage = '';
        
        // 验证目标资源池
        if (!targetPool) {
            errorMessage = '请输入目标资源池';
            hasError = true;
        } else if (!validatePoolFormat(targetPool)) {
            errorMessage = '目标资源池格式错误，请使用"Physical Cluster/IaaS Cluster"格式';
            hasError = true;
        }
        
        // 验证候选资源池
        if (!candidatePools) {
            errorMessage = '请输入至少一个候选资源池';
            hasError = true;
        } else {
            const pools = candidatePools.split(',').map(p => p.trim());
            const invalidPools = pools.filter(p => !validatePoolFormat(p));
            if (invalidPools.length > 0) {
                errorMessage = `以下候选资源池格式错误: ${invalidPools.join(', ')}`;
                hasError = true;
            }
            
            // 检查重复
            const uniquePools = new Set(pools);
            if (uniquePools.size !== pools.length) {
                errorMessage = '候选资源池存在重复';
                hasError = true;
            }
            
            // 检查与目标池相同
            if (pools.includes(targetPool)) {
                errorMessage = '候选资源池不能与目标资源池相同';
                hasError = true;
            }
        }
        
        if (hasError) {
            alert(errorMessage);
            event.preventDefault();
            return;
        }
        
        // 显示加载提示
        showLoadingMessage();
    });
}

/**
 * 初始化实时验证
 */
function initRealTimeValidation() {
    const targetInput = document.getElementById('target_pool');
    const candidateInput = document.getElementById('candidate_pools');
    
    if (targetInput) {
        targetInput.addEventListener('input', function() {
            validatePoolInput(this);
        });
    }
    
    if (candidateInput) {
        candidateInput.addEventListener('input', function() {
            validateCandidatePools(this);
        });
    }
}

/**
 * 验证资源池格式
 */
function validatePoolFormat(pool) {
    const pattern = /^[\w-]+\/[\w-]+$/;
    return pattern.test(pool.trim());
}

/**
 * 验证单个资源池输入
 */
function validatePoolInput(input) {
    const value = input.value.trim();
    if (value && !validatePoolFormat(value)) {
        input.classList.add('is-invalid');
    } else {
        input.classList.remove('is-invalid');
    }
}

/**
 * 验证候选资源池输入
 */
function validateCandidatePools(input) {
    const value = input.value.trim();
    if (!value) return;
    
    const pools = value.split(',').map(p => p.trim()).filter(p => p);
    const hasInvalid = pools.some(p => !validatePoolFormat(p));
    
    if (hasInvalid) {
        input.classList.add('is-invalid');
    } else {
        input.classList.remove('is-invalid');
    }
}

/**
 * 显示加载提示
 */
function showLoadingMessage() {
    const button = document.querySelector('button[type="submit"]');
    if (button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>分析中...';
        button.disabled = true;
    }
}

/**
 * 初始化示例按钮
 */
function initExampleButton() {
    // 添加示例按钮
    const form = document.querySelector('form');
    if (!form) return;
    
    const exampleButton = document.createElement('button');
    exampleButton.type = 'button';
    exampleButton.className = 'btn btn-outline-secondary btn-sm mt-2';
    exampleButton.innerHTML = '<i class="bi bi-lightbulb me-2"></i>加载示例数据';
    
    const candidateGroup = document.querySelector('#candidate_pools').parentElement;
    candidateGroup.appendChild(exampleButton);
    
    exampleButton.addEventListener('click', function() {
        document.getElementById('target_pool').value = 'Oscar/default';
        document.getElementById('candidate_pools').value = 'Zelda/default,Alpha/default,Beta/default';
        document.getElementById('idc').value = 'MY,SH';
    });
}

/**
 * 格式化数字显示
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * 实时字符计数
 */
function initCharCounter() {
    const textarea = document.getElementById('candidate_pools');
    if (!textarea) return;
    
    const counter = document.createElement('small');
    counter.className = 'form-text text-muted';
    counter.id = 'char-counter';
    textarea.parentElement.appendChild(counter);
    
    textarea.addEventListener('input', function() {
        const count = this.value.trim() ? this.value.split(',').length : 0;
        counter.textContent = `已输入 ${count} 个候选资源池`;
    });
}

// 初始化字符计数器
document.addEventListener('DOMContentLoaded', function() {
    initCharCounter();
});
