/**
 * PSM双资源池部署分析工具 - 前端交互脚本
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化主题设置
    initTheme();
    
    // 表单验证
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(event) {
            // 获取资源池输入
            const pool1 = document.getElementById('pool1').value.trim();
            const pool2 = document.getElementById('pool2').value.trim();
            
            // 验证资源池格式
            const poolPattern = /^[\w-]+\/[\w-]+$/;
            let hasError = false;
            
            if (!poolPattern.test(pool1)) {
                alert('第一个资源池格式错误，请使用"Physical Cluster/IaaS Cluster"格式');
                event.preventDefault();
                hasError = true;
            }
            
            if (!poolPattern.test(pool2)) {
                alert('第二个资源池格式错误，请使用"Physical Cluster/IaaS Cluster"格式');
                event.preventDefault();
                hasError = true;
            }
            
            if (!hasError && pool1 === pool2) {
                alert('两个资源池不能相同，请选择不同的资源池');
                event.preventDefault();
            }
            
            // 显示加载提示
            if (!hasError) {
                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 分析中...';
                submitBtn.disabled = true;
            }
        });
    }
    
    // 表格增强功能
    enhanceDataTables();
    
    // 主题切换按钮点击事件
    document.addEventListener('click', function(event) {
        if (event.target.closest('.theme-toggle')) {
            toggleTheme();
        }
    });
});

/**
 * 初始化主题
 */
function initTheme() {
    // 添加主题切换按钮到页面
    if (!document.querySelector('.theme-toggle')) {
        const themeToggle = document.createElement('button');
        themeToggle.className = 'theme-toggle';
        themeToggle.title = '切换主题';
        themeToggle.innerHTML = '<i class="bi bi-circle-half"></i>';
        document.body.appendChild(themeToggle);
    }
    
    // 检查本地存储中的主题设置
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme) {
        // 应用保存的主题
        document.body.className = savedTheme;
    } else {
        // 默认跟随系统主题，不设置特定类名
        document.body.className = '';
    }
    
    // 更新主题图标
    updateThemeIcon();
}

/**
 * 切换主题
 */
function toggleTheme() {
    if (document.body.classList.contains('dark-theme')) {
        // 从深色切换到亮色
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        localStorage.setItem('theme', 'light-theme');
    } else if (document.body.classList.contains('light-theme')) {
        // 从亮色切换到系统默认
        document.body.classList.remove('light-theme');
        localStorage.removeItem('theme');
    } else {
        // 从系统默认切换到深色
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark-theme');
    }
    
    // 更新主题图标
    updateThemeIcon();
}

/**
 * 更新主题图标
 */
function updateThemeIcon() {
    const themeIcon = document.querySelector('.theme-toggle i');
    if (!themeIcon) return;
    
    if (document.body.classList.contains('dark-theme')) {
        themeIcon.className = 'bi bi-moon-stars-fill';
    } else if (document.body.classList.contains('light-theme')) {
        themeIcon.className = 'bi bi-sun-fill';
    } else {
        themeIcon.className = 'bi bi-circle-half';
    }
}

/**
 * 增强DataTables功能
 */
function enhanceDataTables() {
    // 如果在结果页面
    if (document.getElementById('detailTable') && typeof $.fn.dataTable !== 'undefined') {
        // 添加表格行分组功能
        $.fn.dataTable.ext.order['psm-group'] = function (settings, col) {
            return this.api().column(col, {order:'index'}).nodes().map(function (td, i) {
                const row = $(td).closest('tr');
                const psm = row.find('td:first-child').text();
                return psm;
            });
        };
        
        // 添加数值格式化
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
                
                // 添加千位分隔符
                if (thousands) {
                    formatted += parts[0].toString().replace(/\B(?=(\d{3})+(?!\d))/g, thousands);
                } else {
                    formatted += parts[0];
                }
                
                // 添加小数部分
                if (precision > 0 && parts.length > 1) {
                    formatted += (decimal || '.') + parts[1];
                }
                
                return formatted + (postfix || '');
            };
        };
        
        // 添加表格行高亮
        $('#detailTable, #summaryTable').on('mouseenter', 'tbody tr', function() {
            const psm = $(this).find('td:first-child').text();
            $('tbody tr').each(function() {
                if ($(this).find('td:first-child').text() === psm) {
                    $(this).addClass('table-hover');
                }
            });
        }).on('mouseleave', 'tbody tr', function() {
            $('tbody tr').removeClass('table-hover');
        });
    }
}

/**
 * 导出表格数据为CSV
 * @param {string} tableId - 表格ID
 * @param {string} filename - 导出文件名
 */
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // 处理单元格内容，确保CSV格式正确
            let data = cols[j].innerText.replace(/\r?\n/g, ' ').replace(/"/g, '""');
            row.push('"' + data + '"');
        }
        
        csv.push(row.join(','));
    }
    
    // 下载CSV文件
    downloadCSV(csv.join('\n'), filename);
}

/**
 * 下载CSV文件
 * @param {string} csv - CSV内容
 * @param {string} filename - 文件名
 */
function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], {type: 'text/csv;charset=utf-8;'});
    const downloadLink = document.createElement('a');
    
    // 创建下载链接
    downloadLink.href = URL.createObjectURL(csvFile);
    downloadLink.download = filename;
    
    // 触发下载
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}