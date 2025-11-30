const hre = require("hardhat");

async function main() {
  console.log("🚀 Deploying SupplyChain contract to testnet...");

  // Get the deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log("📝 Deploying with account:", deployer.address);

  // Get account balance
  const balance = await deployer.getBalance();
  console.log("💰 Account balance:", hre.ethers.utils.formatEther(balance), "MATIC");

  // Deploy the contract
  const SupplyChain = await hre.ethers.getContractFactory("SupplyChain");
  console.log("⏳ Deploying contract...");
  
  const supplyChain = await SupplyChain.deploy();
  await supplyChain.deployed();

  console.log("✅ SupplyChain deployed to:", supplyChain.address);

  // Wait for a few block confirmations
  console.log("⏳ Waiting for block confirmations...");
  await supplyChain.deployTransaction.wait(5);

  // Verify the contract on Polygonscan
  console.log("🔍 Verifying contract on Polygonscan...");
  try {
    await hre.run("verify:verify", {
      address: supplyChain.address,
      constructorArguments: [],
    });
    console.log("✅ Contract verified successfully");
  } catch (error) {
    console.log("⚠️  Verification failed:", error.message);
  }

  // Save deployment info
  const deploymentInfo = {
    network: hre.network.name,
    contractAddress: supplyChain.address,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    blockNumber: await hre.ethers.provider.getBlockNumber(),
  };

  console.log("\n📋 Deployment Summary:");
  console.log("═══════════════════════════════════════");
  console.log("Network:", deploymentInfo.network);
  console.log("Contract Address:", deploymentInfo.contractAddress);
  console.log("Deployer:", deploymentInfo.deployer);
  console.log("Block Number:", deploymentInfo.blockNumber);
  console.log("Timestamp:", deploymentInfo.timestamp);
  console.log("═══════════════════════════════════════");

  // Save to file
  const fs = require("fs");
  const path = require("path");
  const deploymentsDir = path.join(__dirname, "../deployments");
  
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir);
  }

  const filename = `${hre.network.name}_${Date.now()}.json`;
  fs.writeFileSync(
    path.join(deploymentsDir, filename),
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log(`\n💾 Deployment info saved to: deployments/${filename}`);

  // Example usage
  console.log("\n📖 Example Usage:");
  console.log("═══════════════════════════════════════");
  console.log("// Create a product");
  console.log(`await supplyChain.createProduct(
    "Tomatoes",
    "Cherry",
    123,
    ${Math.floor(Date.now() / 1000)},
    true
  );`);
  console.log("\n// Update stage");
  console.log(`await supplyChain.updateStage(
    1,
    1, // Growing
    "Field A",
    "Healthy growth",
    []
  );`);
  console.log("═══════════════════════════════════════");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
