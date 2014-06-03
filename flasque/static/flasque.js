var flasqueApp = angular.module("flasqueApp", ['ngRoute']);

flasqueApp.run(function($rootScope){
    $rootScope.sse = null;
});

flasqueApp.config(function($routeProvider) {
    $routeProvider
        .when("/", {
            templateUrl: "/static/queues.html",
            controller: "queueController",
            activetab: 'queues',
        })
        .when("/channels", {
            templateUrl: "/static/channels.html",
            controller: "channelController",
            activetab: "channels",
        });
});

flasqueApp.controller('queueController', function($scope, $rootScope, $route) {
    $scope.$route = $route;
    $scope.queues = {};

    if ($rootScope.sse)
        $rootScope.sse.close();

    $rootScope.sse = new EventSource("/status");
    $rootScope.sse.onmessage = function(message){
        if (message.data){
            var data = angular.fromJson(message.data);
            for (e in data) {
                $scope.queues[data[e][0]] = {
                    waiting: data[e][1],
                    pending: data[e][2],
                    done: data[e][3],
                }
            }
            $scope.$apply();
        }
    };
});

flasqueApp.controller('channelController', function($scope, $rootScope, $route) {
    $scope.$route = $route;
    $scope.messages = [];

    if ($rootScope.sse)
        $rootScope.sse.close();

    $rootScope.sse = new EventSource("/channel/");
    $rootScope.sse.onmessage = function(message){
        if (message.data){
            var msg = angular.fromJson(message.data);
            $scope.messages.push(msg);
            $scope.messages = $scope.messages.slice(-30)
            $scope.$apply();
        }
    };
});
