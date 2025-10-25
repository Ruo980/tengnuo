/**
 * PSM双资源池部署分析工具 - 高级前端交互脚本
 */

// 全局配置
const CONFIG = {
    animationDuration: 300,
    debounceDelay: 300,
    toastDuration: 3000
};

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * 初始化应用
 */
function initializeApp() {
    // 初始化表单验证
    initializeFormValidation();
    
    // 初始化UI增强
    initializeUIEnhancements();
    
    // 初始化数据表格增强
    enhanceDataTables();
    
    // 初始化页面动画
    initializeAnimations();
    
    // 初始化工具提示
    initializeTooltips();
    
    console.log('PSM分析工具已初始化完成');
}

/**
 * 初始化表单验证
 */
function initializeFormValidation() {
    const form = document.querySelector('#analysisForm');
    if (!form) return;
    
    // 实时验证
    const pool1Input = document.getElementById('pool1');
    const pool2Input = document.getElementById('pool2');
    
    if (pool1Input) {
        pool1Input.addEventListener('input', debounce(validatePoolInput, CONFIG.debounceDelay));
        pool1Input.addEventListener('blur', validatePoolInput);
    }
    
    if (pool2Input) {
        pool2Input.addEventListener('input', debounce(validatePoolInput, CONFIG.debounceDelay));
        pool2Input.addEventListener('blur', validatePoolInput);
    }
    
    // 表单提交验证
    form.addEventListener('submit', handleFormSubmit);
}

/**
 * 验证资源池输入
 */
function validatePoolInput(event) {
    const input = event.target;
    const value = input.value.trim();
    const poolPattern = /^[\w-]+\/[\w-]+$/;
    
    clearValidationFeedback(input);
    
    if (value && !poolPattern.test(value)) {
        showValidationError(input, '格式错误：请使用 "Physical Cluster/IaaS Cluster" 格式');
        return false;
    }
    
    if (value && poolPattern.test(value)) {
        showValidationSuccess(input, '格式正确');
        return true;
    }
    
    return true;
}

/**
 * 处理表单提交
 */
function handleFormSubmit(event) {
    const pool1 = document.getElementById('pool1').value.trim();
    const pool2 = document.getElementById('pool2').value.trim();
    
    // 验证资源池格式
    const poolPattern = /^[\w-]+\/[\w-]+$/;
    let hasError = false;
    
    if (!poolPattern.test(pool1)) {
        showNotification('第一个资源池格式错误，请使用"Physical Cluster/IaaS Cluster"格式', 'error');
        event.preventDefault();
        hasError = true;
    }
    
    if (!poolPattern.test(pool2)) {
        showNotification('第二个资源池格式错误，请使用"Physical Cluster/IaaS Cluster"格式', 'error');
        event.preventDefault();
        hasError = true;
    }
    
    if (!hasError && pool1 === pool2) {
        showNotification('两个资源池不能相同，请选择不同的资源池', 'warning');
        event.preventDefault();
        hasError = true;
    }
    
    // 显示加载状态
    if (!hasError) {
        showLoadingState();
    }
}

/**
 * 显示验证错误
 */
function showValidationError(input, message) {
    input.classList.add('is-invalid');
    input.classList.remove('is-valid');
    
    let feedback = input.parentNode.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        input.parentNode.appendChild(feedback);
    }
    feedback.textContent = message;
}

/**
 * 显示验证成功
 */
function showValidationSuccess(input, message) {
    input.classList.add('is-valid');
    input.classList.remove('is-invalid');
    
    let feedback = input.parentNode.querySelector('.valid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'valid-feedback';
        input.parentNode.appendChild(feedback);
    }
    feedback.textContent = message;
}

/**
 * 清除验证反馈
 */
function clearValidationFeedback(input) {
    input.classList.remove('is-valid', 'is-invalid');
    
    const feedbacks = input.parentNode.querySelectorAll('.invalid-feedback, .valid-feedback');
    feedbacks.forEach(feedback => feedback.remove());
}

/**
 * 显示加载状态
 */
function showLoadingState() {
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = submitBtn.querySelector('#loadingSpinner');
    
    if (submitBtn && btnText && spinner) {
        btnText.textContent = '分析中...';
        spinner.classList.remove('d-none');
        submitBtn.disabled = true;
        submitBtn.classList.add('loading');
    }
}

/**
 * 填充示例数据
 */
function fillExample(cluster1, cluster2) {
    const pool1Input = document.getElementById('pool1');
    const pool2Input = document.getElementById('pool2');
    
    if (pool1Input && pool2Input) {
        pool1Input.value = `${cluster1}/default`;
        pool2Input.value = `${cluster2}/default`;
        
        // 添加填充动画
        [pool1Input, pool2Input].forEach(input => {
            input.style.transform = 'scale(1.05)';
            input.style.transition = 'transform 0.2s ease';
            setTimeout(() => {
                input.style.transform = 'scale(1)';
            }, 200);
        });
        
        showNotification('已填充示例数据', 'success');
    }
}

/**
 * 初始化UI增强
 */
function initializeUIEnhancements() {
    // 添加输入框聚焦效果
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentNode.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentNode.classList.remove('focused');
        });
    });
    
    // 添加按钮点击波纹效果
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(addRippleEffect);
}

/**
 * 添加波纹效果
 */
function addRippleEffect(button) {
    button.addEventListener('click', function(e) {
        const ripple = document.createElement('div');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;
        
        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    });
}

/**
 * 增强DataTables功能
 */
function enhanceDataTables() {
    if (typeof $.fn.dataTable === 'undefined') return;
    
    // 自定义排序函数
    $.fn.dataTable.ext.order['psm-group'] = function (settings, col) {
        return this.api().column(col, {order:'index'}).nodes().map(function (td, i) {
            const row = $(td).closest('tr');
            const psm = row.find('td:first-child').text();
            return psm;
        });
    };
    
    // 数值格式化渲染器
    $.fn.dataTable.render.number = function(thousands, decimal, precision, prefix, postfix) {
        return function(data, type, row) {
            if (type !== 'display') return data;
            if (typeof data !== 'number' && typeof data !== 'string') return data;
            
            const num = typeof data === 'string' ? parseFloat(data) : data;
            if (isNaN(num)) return data;
            
            const negative = num < 0 ? '-' : '';
            const value = Math.abs(num).toFixed(precision);
            
            const parts = value.split('.');
            let formatted = negative + (prefix || '');
            
            if (thousands) {
                formatted += parts[0].toString().replace(/\B(?=(\d{3})+(?!\d))/g, thousands);
            } else {
                formatted += parts[0];
            }
            
            if (precision > 0 && parts.length > 1) {
                formatted += (decimal || '.') + parts[1];
            }
            
            return formatted + (postfix || '');
        };
    };
    
    // 表格行高亮功能
    $(document).on('mouseenter', '#detailTable tbody tr, #summaryTable tbody tr', function() {
        const psm = $(this).find('td:first-child').text();
        highlightRelatedRows(psm);
    });
    
    $(document).on('mouseleave', '#detailTable tbody tr, #summaryTable tbody tr', function() {
        clearRowHighlight();
    });
}

/**
 * 高亮相关行
 */
function highlightRelatedRows(psm) {
    $('#detailTable tbody tr, #summaryTable tbody tr').each(function() {
        if ($(this).find('td:first-child').text() === psm) {
            $(this).addClass('highlight-related');
        }
    });
}

/**
 * 清除行高亮
 */
function clearRowHighlight() {
    $('#detailTable tbody tr, #summaryTable tbody tr').removeClass('highlight-related');
}

/**
 * 初始化页面动画
 */
function initializeAnimations() {
    // 添加页面加载动画
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 150);
    });
    
    // 添加滚动时的动画
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.glass-card').forEach(card => {
        observer.observe(card);
    });
}

/**
 * 初始化工具提示
 */
function initializeTooltips() {
    // 初始化Bootstrap工具提示
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * 显示通知
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    `;
    
    notification.innerHTML = `
        <i class="bi bi-${getIconByType(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // 自动移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, CONFIG.toastDuration);
}

/**
 * 根据类型获取图标
 */
function getIconByType(type) {
    const icons = {
        success: 'check-circle-fill',
        error: 'exclamation-circle-fill',
        warning: 'exclamation-triangle-fill',
        info: 'info-circle-fill'
    };
    return icons[type] || icons.info;
}

/**
 * 防抖函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 导出表格数据为CSV
 */
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/\r?\n/g, ' ').replace(/"/g, '""');
            row.push('"' + data + '"');
        }
        
        csv.push(row.join(','));
    }
    
    downloadCSV(csv.join('\n'), filename);
}

/**
 * 下载CSV文件
 */
function downloadCSV(csv, filename) {
    const csvFile = new Blob(['\ufeff' + csv], {type: 'text/csv;charset=utf-8;'});
    const downloadLink = document.createElement('a');
    
    downloadLink.href = URL.createObjectURL(csvFile);
    downloadLink.download = filename;
    
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

/**
 * 工具函数：平滑滚动到元素
 */
function smoothScrollTo(element) {
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// 暴露全局函数
window.fillExample = fillExample;
window.exportTableToCSV = exportTableToCSV;
window.smoothScrollTo = smoothScrollTo;
window.showNotification = showNotification;