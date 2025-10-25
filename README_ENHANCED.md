# PSM多资源池部署分析工具 - 增强版

## 功能介绍

增强版在原基础上支持**多个候选资源池**同时分析，提供更灵活的资源腾挪方案选择。主要功能包括：

### 核心增强功能
1. **多资源池支持**：可同时输入多个候选资源池进行分析
2. **智能匹配**：分别计算目标资源池与每个候选池的匹配情况
3. **可视化对比**：直观展示各候选池的匹配结果和资源统计
4. **灵活选择**：用户可根据匹配情况选择最佳腾挪方案
5. **增强报告**：为每个候选池生成独立的分析工作表

### 使用场景
- 资源池A缺少资源，需要寻找多个候选资源池(B/C/D...)进行资源腾挪
- 需要对比不同候选池的可用资源情况
- 优化资源分配策略，选择最优的腾挪方案

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行方式

#### 命令行模式
```bash
python main_enhanced.py
```

#### Web应用模式
```bash
python app_enhanced.py
```
启动后访问：http://localhost:8889

### 使用示例

#### 场景描述
- 目标资源池：Oscar/default（需要借出资源）
- 候选资源池：Zelda/default、Alpha/default、Beta/default（资源充足）

#### 操作步骤
1. 输入目标资源池：`Oscar/default`
2. 输入候选资源池：`Zelda/default,Alpha/default,Beta/default`
3. 系统分别分析每个候选池的匹配情况
4. 查看结果选择最佳腾挪方案

## 详细使用指南

### 输入格式

#### 资源池格式
- 格式：`Physical Cluster/IaaS Cluster`
- 示例：`Oscar/default`、`Zelda/default`

#### 候选资源池输入
- 多个资源池用逗号分隔
- 支持任意数量候选池
- 自动去重和格式验证

### 输出结果

#### Excel报告结构
1. **候选池1_资源池名_汇总**：每个候选池的资源汇总
2. **候选池1_资源池名_详细**：每个候选池的详细数据
3. **资源池统计**：所有资源池的总体统计

#### Web界面展示
- **概览卡片**：目标池和候选池的统计信息
- **匹配结果**：按候选池分组展示匹配情况
- **资源对比**：直观对比各候选池资源状况

### 功能特色

#### 智能排序
- 按目标资源池实例数降序排序
- 优先展示可腾挪资源多的服务

#### 实时验证
- 输入格式实时验证
- 重复资源池自动检测
- 目标池与候选池冲突提示

#### 交互增强
- 示例数据一键加载
- 实时字符计数
- 加载状态提示

## API接口

### 分析接口
```bash
POST /api/analyze
Content-Type: application/json

{
    "idc": "MY,SH",
    "target_pool": "Oscar/default",
    "candidate_pools": "Zelda/default,Alpha/default"
}
```

### 响应格式
```json
{
    "status": "success",
    "data": {
        "target_pool": "Oscar/default",
        "candidate_pools": ["Zelda/default", "Alpha/default"],
        "results": {
            "Zelda/default": {
                "has_matches": true,
                "matching_psm_count": 5,
                "detailed_data": [...],
                "summary_data": [...]
            },
            "Alpha/default": {
                "has_matches": false,
                "matching_psm_count": 0
            }
        }
    }
}
```

## 使用技巧

### 最佳实践
1. **候选池选择**：优先选择资源充足的候选池
2. **批量分析**：可一次性分析5-10个候选池
3. **结果筛选**：重点关注匹配PSM数量多的候选池
4. **资源对比**：结合CPU和内存需求选择合适池

### 常见问题

#### 无匹配结果
- 检查资源池名称是否正确
- 确认PSM服务确实部署在目标池
- 验证机房过滤条件是否过严

#### 格式错误
- 确保使用正确的斜杠分隔
- 检查是否有空格或特殊字符
- 验证物理集群和IaaS集群名称

#### 性能优化
- 减少候选池数量提高分析速度
- 合理使用机房过滤缩小范围
- 分批处理大量候选池

## 项目结构

```
/
├── main_enhanced.py          # 增强版命令行程序
├── app_enhanced.py           # 增强版Web应用
├── templates/
│   ├── index_enhanced.html   # 增强版首页
│   ├── results_enhanced.html # 增强版结果页
│   └── error_enhanced.html   # 增强版错误页
├── static/
│   └── js/
│       └── main_enhanced.js  # 增强版前端脚本
└── README_ENHANCED.md        # 增强版说明文档
```

## 版本对比

| 功能特性 | 基础版 | 增强版 |
|----------|--------|--------|
| 资源池数量 | 2个(固定) | 多个(灵活) |
| 候选池选择 | 单一选择 | 多池对比 |
| 输出报告 | 单一工作表 | 多工作表 |
| 分析维度 | 一对一 | 一对多 |
| 交互体验 | 基础表单 | 实时验证 |
| API支持 | 无 | 完整API |

## 技术支持

### 运行环境
- Python 3.7+
- Flask 2.0+
- pandas 1.3+
- openpyxl 3.0+

### 配置参数
- 端口：8889（避免与基础版冲突）
- 数据源：默认使用all.xlsx
- 输出目录：outputs/

### 故障排除
1. **端口冲突**：修改app_enhanced.py中的端口配置
2. **内存不足**：减少候选池数量或优化过滤条件
3. **格式错误**：使用示例数据验证输入格式

## 更新日志

### v2.0 增强版
- ✅ 支持多个候选资源池
- ✅ 智能匹配和对比
- ✅ 增强版Web界面
- ✅ 实时输入验证
- ✅ 完整API接口
- ✅ 示例数据功能
- ✅ 错误处理优化

