# 🔗 Blockchain Supply Chain

نظام تتبع سلسلة التوريد الزراعية باستخدام Blockchain

## 📋 نظرة عامة

نظام قائم على Blockchain لتتبع المنتجات الزراعية من المزرعة إلى المستهلك بشفافية كاملة. يستخدم Smart Contracts على شبكة Polygon لضمان الموثوقية والشفافية.

## 🎯 الميزات

### 1. تتبع شامل للمنتجات
- تسجيل المنتج من الزراعة
- تتبع جميع مراحل الإنتاج
- سجل غير قابل للتعديل
- شفافية كاملة

### 2. مراحل سلسلة التوريد
1. **Planted** - مرحلة الزراعة
2. **Growing** - مرحلة النمو
3. **Harvested** - مرحلة الحصاد
4. **Processed** - مرحلة المعالجة
5. **Packaged** - مرحلة التعبئة
6. **InTransit** - مرحلة النقل
7. **Delivered** - مرحلة التسليم
8. **Sold** - مرحلة البيع

### 3. الشهادات والتوثيق
- إضافة شهادات عضوية
- توثيق المعايير
- تخزين المستندات على IPFS
- التحقق من الأصالة

### 4. الشفافية
- سجل كامل لكل منتج
- معلومات المزارع
- تواريخ دقيقة
- موقع جغرافي

## 🛠️ التقنيات المستخدمة

- **Solidity** - لغة Smart Contracts
- **Hardhat** - بيئة التطوير
- **Ethers.js** - مكتبة Ethereum
- **Polygon** - شبكة Blockchain
- **IPFS** - تخزين المستندات
- **OpenZeppelin** - مكتبات آمنة

## 📦 التثبيت

```bash
cd blockchain-supply-chain

# تثبيت المكتبات
npm install

# أو باستخدام yarn
yarn install
```

## 🔧 التكوين

### ملف .env

أنشئ ملف `.env` في المجلد الرئيسي:

```env
# Private Keys
PRIVATE_KEY=your_private_key_here

# RPC URLs
POLYGON_RPC_URL=https://polygon-rpc.com
MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com

# API Keys
POLYGONSCAN_API_KEY=your_polygonscan_api_key

# IPFS
IPFS_API_URL=https://ipfs.infura.io:5001
IPFS_API_KEY=your_ipfs_key
```

### hardhat.config.js

```javascript
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: "0.8.19",
  networks: {
    mumbai: {
      url: process.env.MUMBAI_RPC_URL,
      accounts: [process.env.PRIVATE_KEY],
      chainId: 80001
    },
    polygon: {
      url: process.env.POLYGON_RPC_URL,
      accounts: [process.env.PRIVATE_KEY],
      chainId: 137
    }
  },
  etherscan: {
    apiKey: process.env.POLYGONSCAN_API_KEY
  }
};
```

## 🚀 الاستخدام

### تجميع العقود

```bash
npm run compile
```

### تشغيل الاختبارات

```bash
npm test
```

### النشر

#### Local Network

```bash
# تشغيل node محلي
npm run node

# في terminal آخر
npm run deploy:local
```

#### Mumbai Testnet

```bash
npm run deploy:testnet
```

#### Polygon Mainnet

```bash
npm run deploy:mainnet
```

## 📝 أمثلة الاستخدام

### إنشاء منتج جديد

```javascript
const { ethers } = require("hardhat");

async function createProduct() {
  const SupplyChain = await ethers.getContractFactory("SupplyChain");
  const supplyChain = await SupplyChain.attach("CONTRACT_ADDRESS");

  const tx = await supplyChain.createProduct(
    "Tomatoes",           // اسم المنتج
    "Cherry",             // النوع
    123,                  // معرف الحقل
    Math.floor(Date.now() / 1000), // تاريخ الزراعة
    true                  // عضوي
  );

  await tx.wait();
  console.log("Product created!");
}
```

### تحديث مرحلة المنتج

```javascript
async function updateStage() {
  const supplyChain = await ethers.getContractAt("SupplyChain", "CONTRACT_ADDRESS");

  const tx = await supplyChain.updateStage(
    1,                    // معرف المنتج
    2,                    // المرحلة الجديدة (Harvested)
    "Field A, Farm 1",    // الموقع
    "Harvest completed",  // ملاحظات
    ["QmHash123"]         // مستندات IPFS
  );

  await tx.wait();
  console.log("Stage updated!");
}
```

### إضافة شهادة

```javascript
async function addCertification() {
  const supplyChain = await ethers.getContractAt("SupplyChain", "CONTRACT_ADDRESS");

  const tx = await supplyChain.addCertification(
    1,                    // معرف المنتج
    "Organic Certified"   // الشهادة
  );

  await tx.wait();
  console.log("Certification added!");
}
```

### الاستعلام عن منتج

```javascript
async function getProduct() {
  const supplyChain = await ethers.getContractAt("SupplyChain", "CONTRACT_ADDRESS");

  const product = await supplyChain.getProduct(1);
  
  console.log("Product Details:");
  console.log("Name:", product.name);
  console.log("Variety:", product.variety);
  console.log("Farmer:", product.farmer);
  console.log("Current Stage:", product.currentStage);
  console.log("Organic:", product.organic);
}
```

## 🔐 الأمان

### Best Practices

1. **Private Keys** - لا تشارك المفاتيح الخاصة أبداً
2. **Access Control** - استخدام modifiers للصلاحيات
3. **Input Validation** - التحقق من جميع المدخلات
4. **Reentrancy Protection** - حماية من هجمات Reentrancy
5. **Gas Optimization** - تحسين استهلاك Gas

### Audit

العقد يستخدم مكتبات OpenZeppelin المُدققة:
- Access Control
- Security patterns
- Best practices

## 📊 Gas Costs (تقديري)

| العملية | Gas Cost | تكلفة MATIC |
|---------|----------|-------------|
| Deploy Contract | ~2,500,000 | ~$0.50 |
| Create Product | ~150,000 | ~$0.03 |
| Update Stage | ~100,000 | ~$0.02 |
| Add Certification | ~50,000 | ~$0.01 |
| Query Product | 0 (read) | $0.00 |

*الأسعار تقريبية وتعتمد على سعر MATIC*

## 🌐 الشبكات المدعومة

### Polygon Mumbai (Testnet)
- **Chain ID:** 80001
- **RPC:** https://rpc-mumbai.maticvigil.com
- **Explorer:** https://mumbai.polygonscan.com
- **Faucet:** https://faucet.polygon.technology

### Polygon Mainnet
- **Chain ID:** 137
- **RPC:** https://polygon-rpc.com
- **Explorer:** https://polygonscan.com

## 🧪 الاختبار

```bash
# تشغيل جميع الاختبارات
npm test

# اختبار محدد
npx hardhat test test/SupplyChain.test.js

# مع Gas Reporter
REPORT_GAS=true npm test

# Coverage
npm run coverage
```

## 📱 التكامل مع Frontend

### Web3 Integration

```javascript
import { ethers } from 'ethers';
import SupplyChainABI from './abis/SupplyChain.json';

const CONTRACT_ADDRESS = "0x...";

async function connectWallet() {
  if (window.ethereum) {
    const provider = new ethers.providers.Web3Provider(window.ethereum);
    await provider.send("eth_requestAccounts", []);
    const signer = provider.getSigner();
    
    const contract = new ethers.Contract(
      CONTRACT_ADDRESS,
      SupplyChainABI,
      signer
    );
    
    return contract;
  }
}
```

### React Example

```jsx
import { useState, useEffect } from 'react';
import { ethers } from 'ethers';

function ProductTracker({ productId }) {
  const [product, setProduct] = useState(null);

  useEffect(() => {
    async function loadProduct() {
      const contract = await connectWallet();
      const data = await contract.getProduct(productId);
      setProduct(data);
    }
    loadProduct();
  }, [productId]);

  return (
    <div>
      <h2>{product?.name}</h2>
      <p>Farmer: {product?.farmer}</p>
      <p>Stage: {product?.currentStage}</p>
    </div>
  );
}
```

## 🔄 التكامل مع Backend

### Python Example

```python
from web3 import Web3

# Connect to Polygon
w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))

# Load contract
contract_address = "0x..."
contract_abi = [...]  # ABI من ملف JSON

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Query product
product = contract.functions.getProduct(1).call()
print(f"Product: {product}")
```

## 📚 الموارد

- [Solidity Documentation](https://docs.soliditylang.org/)
- [Hardhat Documentation](https://hardhat.org/docs)
- [Polygon Documentation](https://docs.polygon.technology/)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/)
- [Ethers.js Documentation](https://docs.ethers.io/)

## 🚀 الميزات القادمة

- [ ] NFT للمنتجات الفريدة
- [ ] Marketplace للبيع المباشر
- [ ] Oracle integration للأسعار
- [ ] Multi-signature للعمليات الحرجة
- [ ] Batch operations
- [ ] Carbon credits tracking
- [ ] Quality scoring system
- [ ] Automated compliance checks

## 🐛 استكشاف الأخطاء

### المشكلة: "Insufficient funds"
**الحل:** تأكد من وجود MATIC في المحفظة

### المشكلة: "Nonce too high"
**الحل:** أعد تعيين nonce في MetaMask

### المشكلة: "Contract not verified"
**الحل:** استخدم `npm run verify` مع العنوان الصحيح

## 📞 الدعم

للمساعدة أو الإبلاغ عن مشاكل:
- GitHub Issues: https://github.com/kafaat/sahool-project/issues
- Email: support@sahool.com

## 📄 الترخيص

MIT License - انظر ملف LICENSE للتفاصيل
