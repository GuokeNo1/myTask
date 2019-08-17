<?php
$ISPOST = FALSE;
$ISGET = FALSE;
$API = "";
$INFO = {};
if(isset($_POST["API"])){
    $ISPOST = TRUE;
}
if(isset($_GET["API"])){
    $ISGET = TRUE;
}
if($ISGET && $ISPOST){
    die("API ERROR");
}
else if($ISGET){
    $API = $_GET["API"];
}else if($ISPOST){
    $API = $_POST["API"];
}else{
    die("API ERROR");
}
switch($API){
    case "list":break;
    case "add":break;
    case "change":break;
    case "delete":break;
}
?>