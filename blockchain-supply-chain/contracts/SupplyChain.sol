// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SupplyChain
 * @dev Smart contract for agricultural supply chain tracking
 * Tracks products from farm to consumer with transparency
 */
contract SupplyChain {
    
    // Product stages in supply chain
    enum Stage {
        Planted,
        Growing,
        Harvested,
        Processed,
        Packaged,
        InTransit,
        Delivered,
        Sold
    }
    
    // Product struct
    struct Product {
        uint256 id;
        string name;
        string variety;
        uint256 fieldId;
        address farmer;
        uint256 plantedDate;
        uint256 harvestedDate;
        Stage currentStage;
        bool organic;
        string[] certifications;
        mapping(Stage => StageInfo) stageHistory;
        bool exists;
    }
    
    // Stage information
    struct StageInfo {
        uint256 timestamp;
        address actor;
        string location;
        string notes;
        string[] documents; // IPFS hashes
    }
    
    // Events
    event ProductCreated(uint256 indexed productId, address indexed farmer, string name);
    event StageUpdated(uint256 indexed productId, Stage stage, address indexed actor);
    event CertificationAdded(uint256 indexed productId, string certification);
    event OwnershipTransferred(uint256 indexed productId, address indexed from, address indexed to);
    
    // State variables
    mapping(uint256 => Product) public products;
    mapping(address => uint256[]) public farmerProducts;
    mapping(address => bool) public authorizedActors;
    
    uint256 public productCount;
    address public admin;
    
    // Modifiers
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }
    
    modifier onlyAuthorized() {
        require(
            authorizedActors[msg.sender] || msg.sender == admin,
            "Not authorized"
        );
        _;
    }
    
    modifier productExists(uint256 _productId) {
        require(products[_productId].exists, "Product does not exist");
        _;
    }
    
    constructor() {
        admin = msg.sender;
        authorizedActors[msg.sender] = true;
    }
    
    /**
     * @dev Create a new product (called by farmer)
     */
    function createProduct(
        string memory _name,
        string memory _variety,
        uint256 _fieldId,
        uint256 _plantedDate,
        bool _organic
    ) external returns (uint256) {
        productCount++;
        uint256 newProductId = productCount;
        
        Product storage newProduct = products[newProductId];
        newProduct.id = newProductId;
        newProduct.name = _name;
        newProduct.variety = _variety;
        newProduct.fieldId = _fieldId;
        newProduct.farmer = msg.sender;
        newProduct.plantedDate = _plantedDate;
        newProduct.currentStage = Stage.Planted;
        newProduct.organic = _organic;
        newProduct.exists = true;
        
        // Record planted stage
        StageInfo storage plantedInfo = newProduct.stageHistory[Stage.Planted];
        plantedInfo.timestamp = _plantedDate;
        plantedInfo.actor = msg.sender;
        
        farmerProducts[msg.sender].push(newProductId);
        
        emit ProductCreated(newProductId, msg.sender, _name);
        
        return newProductId;
    }
    
    /**
     * @dev Update product stage
     */
    function updateStage(
        uint256 _productId,
        Stage _newStage,
        string memory _location,
        string memory _notes,
        string[] memory _documents
    ) external onlyAuthorized productExists(_productId) {
        Product storage product = products[_productId];
        
        require(
            uint8(_newStage) > uint8(product.currentStage),
            "Cannot move to previous stage"
        );
        
        product.currentStage = _newStage;
        
        StageInfo storage stageInfo = product.stageHistory[_newStage];
        stageInfo.timestamp = block.timestamp;
        stageInfo.actor = msg.sender;
        stageInfo.location = _location;
        stageInfo.notes = _notes;
        stageInfo.documents = _documents;
        
        // Update harvested date if applicable
        if (_newStage == Stage.Harvested) {
            product.harvestedDate = block.timestamp;
        }
        
        emit StageUpdated(_productId, _newStage, msg.sender);
    }
    
    /**
     * @dev Add certification to product
     */
    function addCertification(
        uint256 _productId,
        string memory _certification
    ) external onlyAuthorized productExists(_productId) {
        products[_productId].certifications.push(_certification);
        emit CertificationAdded(_productId, _certification);
    }
    
    /**
     * @dev Get product details
     */
    function getProduct(uint256 _productId)
        external
        view
        productExists(_productId)
        returns (
            uint256 id,
            string memory name,
            string memory variety,
            uint256 fieldId,
            address farmer,
            uint256 plantedDate,
            uint256 harvestedDate,
            Stage currentStage,
            bool organic
        )
    {
        Product storage product = products[_productId];
        return (
            product.id,
            product.name,
            product.variety,
            product.fieldId,
            product.farmer,
            product.plantedDate,
            product.harvestedDate,
            product.currentStage,
            product.organic
        );
    }
    
    /**
     * @dev Get stage information
     */
    function getStageInfo(uint256 _productId, Stage _stage)
        external
        view
        productExists(_productId)
        returns (
            uint256 timestamp,
            address actor,
            string memory location,
            string memory notes
        )
    {
        StageInfo storage info = products[_productId].stageHistory[_stage];
        return (info.timestamp, info.actor, info.location, info.notes);
    }
    
    /**
     * @dev Get product certifications
     */
    function getCertifications(uint256 _productId)
        external
        view
        productExists(_productId)
        returns (string[] memory)
    {
        return products[_productId].certifications;
    }
    
    /**
     * @dev Get farmer's products
     */
    function getFarmerProducts(address _farmer)
        external
        view
        returns (uint256[] memory)
    {
        return farmerProducts[_farmer];
    }
    
    /**
     * @dev Authorize actor
     */
    function authorizeActor(address _actor) external onlyAdmin {
        authorizedActors[_actor] = true;
    }
    
    /**
     * @dev Revoke actor authorization
     */
    function revokeActor(address _actor) external onlyAdmin {
        authorizedActors[_actor] = false;
    }
    
    /**
     * @dev Check if address is authorized
     */
    function isAuthorized(address _actor) external view returns (bool) {
        return authorizedActors[_actor];
    }
}
