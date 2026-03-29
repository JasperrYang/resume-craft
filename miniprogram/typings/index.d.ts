/// <reference path="./typings/index.d.ts" />

interface IAppOption {
  globalData: {
    userInfo: any;
    token: string;
    baseUrl: string;
  };
  login(): Promise<any>;
}
