# MAX 源码导入适配层

## 目的
用于接收合法来源的 MAX Android 源码，并执行方案 A 汉化流程。

## 导入检查
- Android Gradle 工程
- app/src/main/res/values
- app/src/main/res/values-*
- strings.xml
- Compose StringResource

## 汉化流程
1. 导入源码
2. 运行工程扫描
3. 匹配俄文资源
4. 生成 values-zh-rCN
5. 执行构建测试

注意：仅处理用户拥有权限或公开授权的源码。
